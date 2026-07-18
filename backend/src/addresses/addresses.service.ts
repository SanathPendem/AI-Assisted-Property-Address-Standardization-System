import { Injectable, Logger, NotFoundException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { ConfigService } from '@nestjs/config';
import { RawAddress } from '../database/entities/raw-address.entity';
import { CanonicalAddress } from '../database/entities/canonical-address.entity';
import { StandardizationResult } from '../database/entities/standardization-result.entity';
import { ReviewQueue } from '../database/entities/review-queue.entity';
import { AuditTrail } from '../database/entities/audit-trail.entity';
import { MlClientService } from '../ml/ml-client.service';
import { MlService } from '../ml/ml.service';
import { StandardizeAddressDto, PaginationDto } from '../common/dto';

@Injectable()
export class AddressesService {
  private readonly logger = new Logger(AddressesService.name);
  private readonly autoAcceptThreshold: number;
  private readonly reviewThreshold: number;

  constructor(
    @InjectRepository(RawAddress)
    private readonly rawAddressRepo: Repository<RawAddress>,
    @InjectRepository(CanonicalAddress)
    private readonly canonicalRepo: Repository<CanonicalAddress>,
    @InjectRepository(StandardizationResult)
    private readonly resultRepo: Repository<StandardizationResult>,
    @InjectRepository(ReviewQueue)
    private readonly reviewQueueRepo: Repository<ReviewQueue>,
    @InjectRepository(AuditTrail)
    private readonly auditRepo: Repository<AuditTrail>,
    private readonly mlClient: MlClientService,
    private readonly mlService: MlService,
    private readonly config: ConfigService,
  ) {
    this.autoAcceptThreshold = parseFloat(config.get('AUTO_ACCEPT_THRESHOLD', '0.80'));
    this.reviewThreshold = parseFloat(config.get('REVIEW_THRESHOLD', '0.50'));
  }

  async standardize(dto: StandardizeAddressDto) {
    // 1. Call ML service
    const mlResult = await this.mlClient.standardize(dto.rawAddress);

    // 2. Determine routing
    const confidence = mlResult.confidence_score;
    let routingDecision: 'auto_accepted' | 'pending_review' | 'flagged';
    if (confidence >= this.autoAcceptThreshold) {
      routingDecision = 'auto_accepted';
    } else if (confidence >= this.reviewThreshold) {
      routingDecision = 'pending_review';
    } else {
      routingDecision = 'flagged';
    }

    // 3. Save raw address
    const rawAddress = this.rawAddressRepo.create({
      rawText: dto.rawAddress,
      sourceSystem: dto.sourceSystem,
      sourceRecordId: dto.sourceRecordId,
      parsedComponents: mlResult.parsed_components,
    });
    await this.rawAddressRepo.save(rawAddress);

    // 4. Find or create canonical address (only if auto-accepted)
    let canonicalId: string | null = null;
    if (routingDecision === 'auto_accepted') {
      const canonical = await this.findOrCreateCanonical(mlResult);
      canonicalId = canonical.id;
      rawAddress.canonicalId = canonical.id;
      await this.rawAddressRepo.save(rawAddress);
    }

    // 5. Save standardization result
    const modelVersion = await this.mlService.getActiveModelVersion();
    const result = this.resultRepo.create({
      rawAddressId: rawAddress.id,
      canonicalId,
      predictedAddress: mlResult.standardized_address,
      confidenceScore: confidence,
      routingDecision,
      featureVector: mlResult.feature_vector,
      modelVersion,
      processingTimeMs: mlResult.processing_time_ms,
    });
    await this.resultRepo.save(result);

    // 6. If needs review, add to queue
    if (routingDecision === 'pending_review' || routingDecision === 'flagged') {
      // Calculate active-learning priority (higher = more valuable for labeling)
      // Items near the decision boundary are most informative
      const priorityScore = 1.0 - Math.abs(confidence - 0.65);
      const reviewItem = this.reviewQueueRepo.create({
        standardizationId: result.id,
        rawAddressId: rawAddress.id,
        rawAddressText: dto.rawAddress,
        predictedAddress: mlResult.standardized_address,
        confidenceScore: confidence,
        routingDecision,
        priorityScore,
        contextNotes: routingDecision === 'flagged'
          ? 'Low confidence match — requires manual resolution. Review parsed components carefully.'
          : 'Medium confidence match — verify the standardized address is correct.',
      });
      await this.reviewQueueRepo.save(reviewItem);
    }

    // 7. Audit trail
    await this.auditRepo.save(this.auditRepo.create({
      eventType: 'standardized',
      rawAddressId: rawAddress.id,
      rawAddressText: dto.rawAddress,
      predictedAddress: mlResult.standardized_address,
      finalAddress: routingDecision === 'auto_accepted' ? mlResult.standardized_address : null,
      confidenceScore: confidence,
      routingDecision,
      modelVersion,
      metadata: { processingTimeMs: mlResult.processing_time_ms, sourceSystem: dto.sourceSystem },
    }));

    return {
      id: result.id,
      rawAddressId: rawAddress.id,
      rawAddress: dto.rawAddress,
      standardizedAddress: mlResult.standardized_address,
      confidenceScore: confidence,
      routingDecision,
      parsedComponents: mlResult.parsed_components,
      canonicalComponents: mlResult.canonical_components,
      modelVersion,
      processingTimeMs: mlResult.processing_time_ms,
    };
  }

  private async findOrCreateCanonical(mlResult: any): Promise<CanonicalAddress> {
    const cc = mlResult.canonical_components;
    const normalizedKey = this.buildNormalizedKey(cc);

    let canonical = await this.canonicalRepo.findOne({ where: { normalizedKey } });
    if (canonical) {
      canonical.sourceCount += 1;
      await this.canonicalRepo.save(canonical);
      return canonical;
    }

    // Call embedding endpoint if available
    let embedding: number[] | null = null;
    try {
      embedding = await this.mlClient.getEmbedding(mlResult.standardized_address);
    } catch (e) {
      this.logger.warn(`Could not compute embedding for canonical address: ${e.message}`);
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
      // Store embedding as raw string for pgvector format eg '[0.1, 0.2, ...]'
      canonical.embedding = `[${embedding.join(',')}]` as any;
    }
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

  async findAll(pagination: PaginationDto) {
    const page = pagination?.page ?? 1;
    const limit = pagination?.limit ?? 20;
    const [items, total] = await this.resultRepo.findAndCount({
      relations: ['rawAddress', 'canonical'],
      order: { createdAt: 'DESC' },
      skip: (page - 1) * limit,
      take: limit,
    });

    return {
      items,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }

  async findOne(id: string) {
    const result = await this.resultRepo.findOne({
      where: { id },
      relations: ['rawAddress', 'canonical'],
    });
    if (!result) throw new NotFoundException(`Result ${id} not found`);
    return result;
  }
}
