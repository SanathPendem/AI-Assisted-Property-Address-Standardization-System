import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { ModelRegistry } from '../database/entities/model-registry.entity';
import { Feedback } from '../database/entities/feedback.entity';
import { AuditTrail } from '../database/entities/audit-trail.entity';
import { MlClientService } from './ml-client.service';

@Injectable()
export class MlService {
  private readonly logger = new Logger(MlService.name);

  constructor(
    @InjectRepository(ModelRegistry)
    private readonly modelRepo: Repository<ModelRegistry>,
    @InjectRepository(Feedback)
    private readonly feedbackRepo: Repository<Feedback>,
    @InjectRepository(AuditTrail)
    private readonly auditRepo: Repository<AuditTrail>,
    private readonly mlClient: MlClientService,
  ) {}

  async triggerRetrain() {
    // Fetch unused feedback
    const unusedFeedback = await this.feedbackRepo.find({
      where: { usedInTraining: false },
      order: { createdAt: 'ASC' },
    });

    if (unusedFeedback.length === 0) {
      return { message: 'No new feedback available for retraining', feedbackCount: 0 };
    }

    this.logger.log(`Triggering retrain with ${unusedFeedback.length} feedback items`);

    const feedbackData = unusedFeedback.map((f) => ({
      raw_address: f.rawAddressText,
      original_prediction: f.originalPrediction,
      human_decision: f.humanDecision,
      corrected_address: f.correctedAddress,
    }));

    const result = await this.mlClient.triggerRetrain(feedbackData);

    // Mark feedback as used
    const ids = unusedFeedback.map((f) => f.id);
    await this.feedbackRepo
      .createQueryBuilder()
      .update(Feedback)
      .set({ usedInTraining: true, trainingBatchId: result.model_version })
      .whereInIds(ids)
      .execute();

    // Register new model
    await this.modelRepo.update({ isActive: true }, { isActive: false });
    const newModel = this.modelRepo.create({
      version: result.model_version,
      artifactPath: '/app/models/lgbm_model.pkl',
      trainingSamples: result.metrics.training_samples,
      accuracy: result.metrics.accuracy,
      precisionScore: result.metrics.precision,
      recallScore: result.metrics.recall,
      f1Score: result.metrics.f1,
      isActive: true,
    });
    await this.modelRepo.save(newModel);

    // Audit
    await this.auditRepo.save(this.auditRepo.create({
      eventType: 'model_retrained',
      modelVersion: result.model_version,
      metadata: { feedbackCount: unusedFeedback.length, metrics: result.metrics },
    }));

    return {
      message: 'Retraining completed',
      modelVersion: result.model_version,
      feedbackUsed: unusedFeedback.length,
      metrics: result.metrics,
    };
  }

  async getModelStatus() {
    const activeModel = await this.modelRepo.findOne({ where: { isActive: true } });
    const unusedFeedbackCount = await this.feedbackRepo.count({ where: { usedInTraining: false } });
    const totalFeedback = await this.feedbackRepo.count();

    let remoteMetrics = null;
    try {
      remoteMetrics = await this.mlClient.getModelMetrics();
    } catch (e) {
      this.logger.warn('Could not fetch remote ML metrics');
    }

    return {
      activeModel,
      pendingFeedback: unusedFeedbackCount,
      totalFeedback,
      remoteMetrics,
    };
  }

  async getActiveModelVersion(): Promise<string> {
    const model = await this.modelRepo.findOne({ where: { isActive: true } });
    return model?.version ?? 'v0.0.0-baseline';
  }
}
