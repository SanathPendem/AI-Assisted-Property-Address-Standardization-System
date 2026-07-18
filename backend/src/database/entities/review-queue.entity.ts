import {
  Entity, PrimaryGeneratedColumn, Column, CreateDateColumn,
  ManyToOne, JoinColumn, OneToOne, OneToMany,
} from 'typeorm';
import { StandardizationResult } from './standardization-result.entity';
import { RawAddress } from './raw-address.entity';
import { Feedback } from './feedback.entity';

@Entity('review_queue')
export class ReviewQueue {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @OneToOne(() => StandardizationResult, (s) => s.reviewQueueItem)
  @JoinColumn({ name: 'standardization_id' })
  standardizationResult: StandardizationResult;

  @Column({ name: 'standardization_id', type: 'uuid' })
  standardizationId: string;

  @ManyToOne(() => RawAddress, (r) => r.reviewQueueItems)
  @JoinColumn({ name: 'raw_address_id' })
  rawAddress: RawAddress;

  @Column({ name: 'raw_address_id', type: 'uuid' })
  rawAddressId: string;

  @Column({ name: 'raw_address_text', type: 'text' })
  rawAddressText: string;

  @Column({ name: 'predicted_address', type: 'text' })
  predictedAddress: string;

  @Column({ name: 'confidence_score', type: 'numeric', precision: 5, scale: 4 })
  confidenceScore: number;

  @Column({ name: 'routing_decision', type: 'enum', enum: ['auto_accepted', 'pending_review', 'flagged'] })
  routingDecision: string;

  @Column({ name: 'priority_score', type: 'numeric', precision: 5, scale: 4, default: 0.5 })
  priorityScore: number;

  @Column({ name: 'review_status', type: 'enum', enum: ['pending', 'accepted', 'corrected', 'rejected', 'escalated'], default: 'pending' })
  reviewStatus: string;

  @Column({ name: 'reviewer_id', type: 'varchar', nullable: true })
  reviewerId?: string | null;

  @Column({ name: 'reviewed_at', type: 'timestamptz', nullable: true })
  reviewedAt?: Date | null;

  @Column({ name: 'similar_canonicals', type: 'jsonb', nullable: true })
  similarCanonicals?: any[] | null;

  @Column({ name: 'context_notes', type: 'text', nullable: true })
  contextNotes?: string | null;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @OneToMany(() => Feedback, (f) => f.reviewQueueItem)
  feedbackItems: Feedback[];
}
