import {
  Entity, PrimaryGeneratedColumn, Column, CreateDateColumn,
  ManyToOne, JoinColumn, OneToMany,
} from 'typeorm';
import { CanonicalAddress } from './canonical-address.entity';
import { StandardizationResult } from './standardization-result.entity';
import { ReviewQueue } from './review-queue.entity';
import { Feedback } from './feedback.entity';
import { AuditTrail } from './audit-trail.entity';

@Entity('raw_addresses')
export class RawAddress {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'raw_text', type: 'text' })
  rawText: string;

  @Column({ name: 'source_system', nullable: true })
  sourceSystem: string;

  @Column({ name: 'source_record_id', nullable: true })
  sourceRecordId: string;

  @Column({ name: 'parsed_components', type: 'jsonb', nullable: true })
  parsedComponents: Record<string, any>;

  @ManyToOne(() => CanonicalAddress, (c) => c.rawAddresses, { nullable: true })
  @JoinColumn({ name: 'canonical_id' })
  canonical: CanonicalAddress;

  @Column({ name: 'canonical_id', nullable: true })
  canonicalId: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @OneToMany(() => StandardizationResult, (r) => r.rawAddress)
  standardizationResults: StandardizationResult[];

  @OneToMany(() => ReviewQueue, (r) => r.rawAddress)
  reviewQueueItems: ReviewQueue[];

  @OneToMany(() => Feedback, (f) => f.rawAddress)
  feedbackItems: Feedback[];

  @OneToMany(() => AuditTrail, (a) => a.rawAddress)
  auditTrailEntries: AuditTrail[];
}
