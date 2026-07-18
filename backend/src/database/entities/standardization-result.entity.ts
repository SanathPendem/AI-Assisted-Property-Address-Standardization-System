import {
  Entity, PrimaryGeneratedColumn, Column, CreateDateColumn,
  ManyToOne, JoinColumn, OneToOne,
} from 'typeorm';
import { RawAddress } from './raw-address.entity';
import { CanonicalAddress } from './canonical-address.entity';
import { ReviewQueue } from './review-queue.entity';

@Entity('standardization_results')
export class StandardizationResult {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @ManyToOne(() => RawAddress, (r) => r.standardizationResults)
  @JoinColumn({ name: 'raw_address_id' })
  rawAddress: RawAddress;

  @Column({ name: 'raw_address_id', type: 'uuid' })
  rawAddressId: string;

  @ManyToOne(() => CanonicalAddress, (c) => c.standardizationResults, { nullable: true })
  @JoinColumn({ name: 'canonical_id' })
  canonical?: CanonicalAddress | null;

  @Column({ name: 'canonical_id', type: 'uuid', nullable: true })
  canonicalId?: string | null;

  @Column({ name: 'predicted_address', type: 'text' })
  predictedAddress: string;

  @Column({ name: 'confidence_score', type: 'numeric', precision: 5, scale: 4 })
  confidenceScore: number;

  @Column({ name: 'routing_decision', type: 'enum', enum: ['auto_accepted', 'pending_review', 'flagged'] })
  routingDecision: string;

  @Column({ name: 'feature_vector', type: 'jsonb', nullable: true })
  featureVector?: Record<string, any> | null;

  @Column({ name: 'model_version', type: 'varchar', nullable: true })
  modelVersion?: string | null;

  @Column({ name: 'processing_time_ms', type: 'integer', nullable: true })
  processingTimeMs?: number | null;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @OneToOne(() => ReviewQueue, (r) => r.standardizationResult)
  reviewQueueItem: ReviewQueue;
}
