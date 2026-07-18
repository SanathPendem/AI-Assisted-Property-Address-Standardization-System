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
  rawAddress: RawAddress;

  @Column({ name: 'raw_address_id', nullable: true })
  rawAddressId: string;

  @Column({ name: 'raw_address_text', type: 'text', nullable: true })
  rawAddressText: string;

  @Column({ name: 'predicted_address', type: 'text', nullable: true })
  predictedAddress: string;

  @Column({ name: 'final_address', type: 'text', nullable: true })
  finalAddress: string;

  @Column({ name: 'confidence_score', type: 'numeric', precision: 5, scale: 4, nullable: true })
  confidenceScore: number;

  @Column({ name: 'routing_decision', type: 'enum', enum: ['auto_accepted', 'pending_review', 'flagged'], nullable: true })
  routingDecision: string;

  @Column({ name: 'human_decision', type: 'enum', enum: ['accepted', 'corrected', 'rejected'], nullable: true })
  humanDecision: string;

  @Column({ name: 'human_rationale', type: 'text', nullable: true })
  humanRationale: string;

  @Column({ name: 'reviewer_id', nullable: true })
  reviewerId: string;

  @Column({ name: 'model_version', nullable: true })
  modelVersion: string;

  @Column({ type: 'jsonb', nullable: true })
  metadata: Record<string, any>;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;
}
