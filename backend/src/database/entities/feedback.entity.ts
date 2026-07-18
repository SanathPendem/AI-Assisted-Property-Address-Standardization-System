import {
  Entity, PrimaryGeneratedColumn, Column, CreateDateColumn,
  ManyToOne, JoinColumn,
} from 'typeorm';
import { ReviewQueue } from './review-queue.entity';
import { RawAddress } from './raw-address.entity';

@Entity('feedback')
export class Feedback {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @ManyToOne(() => ReviewQueue, (r) => r.feedbackItems, { nullable: true })
  @JoinColumn({ name: 'review_queue_id' })
  reviewQueueItem: ReviewQueue;

  @Column({ name: 'review_queue_id', nullable: true })
  reviewQueueId: string;

  @ManyToOne(() => RawAddress, (r) => r.feedbackItems)
  @JoinColumn({ name: 'raw_address_id' })
  rawAddress: RawAddress;

  @Column({ name: 'raw_address_id' })
  rawAddressId: string;

  @Column({ name: 'raw_address_text', type: 'text' })
  rawAddressText: string;

  @Column({ name: 'original_prediction', type: 'text' })
  originalPrediction: string;

  @Column({ name: 'human_decision', type: 'enum', enum: ['accepted', 'corrected', 'rejected'] })
  humanDecision: string;

  @Column({ name: 'corrected_address', type: 'text', nullable: true })
  correctedAddress: string;

  @Column({ name: 'reviewer_id' })
  reviewerId: string;

  @Column({ type: 'text', nullable: true })
  rationale: string;

  @Column({ name: 'used_in_training', default: false })
  usedInTraining: boolean;

  @Column({ name: 'training_batch_id', nullable: true })
  trainingBatchId: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;
}
