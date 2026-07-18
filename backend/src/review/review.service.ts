import { Injectable, Logger, NotFoundException, BadRequestException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { ReviewQueue } from '../database/entities/review-queue.entity';
import { Feedback } from '../database/entities/feedback.entity';
import { RawAddress } from '../database/entities/raw-address.entity';
import { CanonicalAddress } from '../database/entities/canonical-address.entity';
import { StandardizationResult } from '../database/entities/standardization-result.entity';
import { AuditTrail } from '../database/entities/audit-trail.entity';
import { MlClientService } from '../ml/ml-client.service';
import { MlService } from '../ml/ml.service';
import { ReviewDecisionDto, PaginationDto, HumanDecision } from '../common/dto';

@Injectable()
export class ReviewService {
  private readonly logger = new Logger(ReviewService.name);

  constructor(
    @InjectRepository(ReviewQueue)
    private readonly reviewRepo: Repository<ReviewQueue>,
    @InjectRepository(Feedback)
    private readonly feedbackRepo: Repository<Feedback>,
    @InjectRepository(RawAddress)
    private readonly rawAddressRepo: Repository<RawAddress>,
    @InjectRepository(CanonicalAddress)
    private readonly canonicalRepo: Repository<CanonicalAddress>,
    @InjectRepository(StandardizationResult)
    private readonly resultRepo: Repository<StandardizationResult>,
    @InjectRepository(AuditTrail)
    private readonly auditRepo: Repository<AuditTrail>,
    private readonly mlClient: MlClientService,
    private readonly mlService: MlService,
  ) {}

  async getQueue(pagination: PaginationDto, status = 'pending') {
    const page = pagination?.page ?? 1;
    const limit = pagination?.limit ?? 10;
    const [items, total] = await this.reviewRepo.findAndCount({
      where: { reviewStatus: status },
      relations: ['rawAddress', 'standardizationResult'],
      order: { priorityScore: 'DESC', createdAt: 'DESC' },
      skip: (page - 1) * limit,
      take: limit,
    });

    // For pending items, dynamically find similar canonicals in database if not set
    for (const item of items) {
      if (item.reviewStatus === 'pending' && (!item.similarCanonicals || item.similarCanonicals.length === 0)) {
        item.similarCanonicals = await this.findSimilarCanonicals(item.rawAddressText);
        await this.reviewRepo.save(item);
      }
    }

    return {
      items,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async decide(id: string, dto: ReviewDecisionDto) {
    const queueItem = await this.reviewRepo.findOne({
      where: { id },
      relations: ['rawAddress', 'standardizationResult'],
    });
    if (!queueItem) throw new NotFoundException(`Queue item ${id} not found`);
    if (queueItem.reviewStatus !== 'pending') throw new BadRequestException(`Queue item has already been resolved`);

    const modelVersion = await this.mlService.getActiveModelVersion();
    let finalAddress = queueItem.predictedAddress;

    if (dto.decision === HumanDecision.CORRECTED) {
      if (!dto.correctedAddress) throw new BadRequestException('Corrected address must be provided when decision is corrected');
      finalAddress = dto.correctedAddress;
    }

    // 1. Update queue item status
    queueItem.reviewStatus = dto.decision;
    queueItem.reviewerId = dto.reviewerId;
    queueItem.reviewedAt = new Date();
    await this.reviewRepo.save(queueItem);

    // 2. Link canonical address (if accepted or corrected)
    let canonicalId: string | null = null;
    if (dto.decision !== HumanDecision.REJECTED) {
      const canonical = await this.findOrCreateCanonicalFromText(finalAddress);
      canonicalId = canonical.id;

      // Update RawAddress linkage
      await this.rawAddressRepo.update({ id: queueItem.rawAddressId }, { canonicalId });
      // Update StandardizationResult linkage
      await this.resultRepo.update({ id: queueItem.standardizationId }, { canonicalId });
    }

    // 3. Create feedback entry for retraining
    const feedback = this.feedbackRepo.create({
      reviewQueueId: queueItem.id,
      rawAddressId: queueItem.rawAddressId,
      rawAddressText: queueItem.rawAddressText,
      originalPrediction: queueItem.predictedAddress,
      humanDecision: dto.decision,
      correctedAddress: dto.decision === HumanDecision.CORRECTED ? dto.correctedAddress : null,
      reviewerId: dto.reviewerId,
      rationale: dto.rationale,
      usedInTraining: false,
    });
    await this.feedbackRepo.save(feedback);

    // 4. Record audit trail
    await this.auditRepo.save(this.auditRepo.create({
      eventType: 'reviewed',
      rawAddressId: queueItem.rawAddressId,
      rawAddressText: queueItem.rawAddressText,
      predictedAddress: queueItem.predictedAddress,
      finalAddress: dto.decision === HumanDecision.REJECTED ? null : finalAddress,
      confidenceScore: queueItem.confidenceScore,
      routingDecision: queueItem.routingDecision,
      humanDecision: dto.decision,
      humanRationale: dto.rationale,
      reviewerId: dto.reviewerId,
      modelVersion,
      metadata: { queueItemId: queueItem.id, feedbackId: feedback.id },
    }));

    // 5. Trigger retraining check: if feedback count reaches 50, trigger retrain automatically
    const unusedFeedbackCount = await this.feedbackRepo.count({ where: { usedInTraining: false } });
    if (unusedFeedbackCount >= 50) {
      this.logger.log(`Unused feedback count (${unusedFeedbackCount}) >= 50. Triggering model retraining...`);
      this.mlService.triggerRetrain().catch(err => {
        this.logger.error(`Auto retraining failed: ${err.message}`);
      });
    }

    return {
      message: 'Decision saved successfully',
      queueItemId: queueItem.id,
      decision: dto.decision,
      canonicalId,
    };
  }

  private async findOrCreateCanonicalFromText(addressText: string): Promise<CanonicalAddress> {
    // Attempt standard parse to construct components if possible, or fallback to simple insert
    let mlResult: any = null;
    try {
      mlResult = await this.mlClient.standardize(addressText);
    } catch (e) {
      this.logger.warn(`Could not parse corrected address through ML service: ${e.message}`);
    }

    if (mlResult) {
      const cc = mlResult.canonical_components;
      const normalizedKey = this.buildNormalizedKey(cc);
      let canonical = await this.canonicalRepo.findOne({ where: { normalizedKey } });
      if (canonical) {
        canonical.sourceCount += 1;
        await this.canonicalRepo.save(canonical);
        return canonical;
      }

      let embedding: number[] | null = null;
      try {
        embedding = await this.mlClient.getEmbedding(addressText);
      } catch (e) {
        this.logger.warn(`Could not compute embedding: ${e.message}`);
      }

      canonical = this.canonicalRepo.create({
        houseNumber: cc.house_number,
        preDirectional: cc.pre_directional,
        streetName: cc.street_name,
        streetSuffix: cc.street_suffix,
        postDirectional: cc.post_directional,
        unitType: cc.unit_type,
        unitNumber: cc.unit_number,
        city: cc.city,
        state: cc.state,
        stateAbbr: cc.state_abbr,
        zipCode: cc.zip_code,
        fullAddress: mlResult.standardized_address,
        normalizedKey,
        sourceCount: 1,
      });
      if (embedding && embedding.length > 0) {
        canonical.embedding = `[${embedding.join(',')}]` as any;
      }
      await this.canonicalRepo.save(canonical);
      return canonical;
    }

    // Fallback if parsing service fails completely
    const normalizedKey = addressText.toLowerCase().replace(/[^a-z0-9]/g, '');
    let canonical = await this.canonicalRepo.findOne({ where: { normalizedKey } });
    if (canonical) {
      canonical.sourceCount += 1;
      await this.canonicalRepo.save(canonical);
      return canonical;
    }
    canonical = this.canonicalRepo.create({
      fullAddress: addressText,
      normalizedKey,
      sourceCount: 1,
    });
    await this.canonicalRepo.save(canonical);
    return canonical;
  }

  private buildNormalizedKey(components: any): string {
    const parts = [
      components.house_number,
      components.pre_directional,
      components.street_name,
      components.street_suffix,
      components.unit_type,
      components.unit_number,
      components.city,
      components.state_abbr,
      components.zip_code,
    ].filter(Boolean).map(s => s.toLowerCase().trim());
    return parts.join('|');
  }

  private async findSimilarCanonicals(addressText: string): Promise<any[]> {
    try {
      const embedding = await this.mlClient.getEmbedding(addressText);
      if (!embedding || embedding.length === 0) return [];

      // Query database using cosine distance (<=> operator in pgvector)
      const vectorStr = `[${embedding.join(',')}]`;
      const matches = await this.canonicalRepo
        .createQueryBuilder('c')
        .select([
          'c.id as id',
          'c.full_address as "fullAddress"',
          'c.city as city',
          'c.state_abbr as "stateAbbr"',
          'c.zip_code as "zipCode"',
          `1 - (c.embedding <=> :vector) as similarity`,
        ])
        .setParameter('vector', vectorStr)
        .orderBy('c.embedding <=> :vector', 'ASC')
        .limit(5)
        .getRawMany();

      return matches.map(m => ({
        id: m.id,
        fullAddress: m.fullAddress,
        city: m.city,
        stateAbbr: m.stateAbbr,
        zipCode: m.zipCode,
        similarity: parseFloat(m.similarity || '0'),
      }));
    } catch (e) {
      this.logger.error(`Cosine similarity lookup failed: ${e.message}`);
      // Simple fallback text matching
      try {
        const matches = await this.canonicalRepo.find({
          take: 5,
        });
        return matches.map(m => ({
          id: m.id,
          fullAddress: m.fullAddress,
          city: m.city,
          stateAbbr: m.stateAbbr,
          zipCode: m.zipCode,
          similarity: 0.5,
        }));
      } catch {
        return [];
      }
    }
  }
}
