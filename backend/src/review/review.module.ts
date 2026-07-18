import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ReviewQueue } from '../database/entities/review-queue.entity';
import { Feedback } from '../database/entities/feedback.entity';
import { RawAddress } from '../database/entities/raw-address.entity';
import { CanonicalAddress } from '../database/entities/canonical-address.entity';
import { StandardizationResult } from '../database/entities/standardization-result.entity';
import { AuditTrail } from '../database/entities/audit-trail.entity';
import { MlModule } from '../ml/ml.module';
import { ReviewController } from './review.controller';
import { ReviewService } from './review.service';

@Module({
  imports: [
    TypeOrmModule.forFeature([
      ReviewQueue,
      Feedback,
      RawAddress,
      CanonicalAddress,
      StandardizationResult,
      AuditTrail,
    ]),
    MlModule,
  ],
  controllers: [ReviewController],
  providers: [ReviewService],
  exports: [ReviewService],
})
export class ReviewModule {}
