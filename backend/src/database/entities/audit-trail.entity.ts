import {
  Entity, PrimaryGeneratedColumn, Column, CreateDateColumn,
  ManyToOne, JoinColumn,
} from 'typeorm';
import { RawAddress } from './raw-address.entity';

@Entity('audit_trail')
export class AuditTrail {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'event_type' })
  eventType: string;

  @ManyToOne(() => RawAddress, (r) => r.auditTrailEntries, { nullable: true })
  @JoinColumn({ name: 'raw_address_id' })
  rawAddress?: RawAddress | null;

  @Column({ name: 'raw_address_id', nullable: true })
  rawAddressId?: string | null;

  @Column({ name: 'raw_address_text', type: 'text', nullable: true })
  rawAddressText?: string | null;

  @Column({ name: 'predicted_address', type: 'text', nullable: true })
  predictedAddress?: string | null;

  @Column({ name: 'final_address', type: 'text', nullable: true })
  finalAddress?: string | null;

  @Column({ name: 'confidence_score', type: 'numeric', precision: 5, scale: 4, nullable: true })
  confidenceScore?: number | null;

  @Column({ name: 'routing_decision', type: 'enum', enum: ['auto_accepted', 'pending_review', 'flagged'], nullable: true })
  routingDecision?: string | null;

  @Column({ name: 'human_decision', type: 'enum', enum: ['accepted', 'corrected', 'rejected'], nullable: true })
  humanDecision?: string | null;

  @Column({ name: 'human_rationale', type: 'text', nullable: true })
  humanRationale?: string | null;

  @Column({ name: 'reviewer_id', nullable: true })
  reviewerId?: string | null;

  @Column({ name: 'model_version', nullable: true })
  modelVersion?: string | null;

  @Column({ type: 'jsonb', nullable: true })
  metadata?: Record<string, any> | null;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;
}
