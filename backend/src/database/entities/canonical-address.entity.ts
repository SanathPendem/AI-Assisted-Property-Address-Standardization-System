import {
  Entity, PrimaryGeneratedColumn, Column, CreateDateColumn,
  UpdateDateColumn, OneToMany,
} from 'typeorm';
import { RawAddress } from './raw-address.entity';
import { StandardizationResult } from './standardization-result.entity';

@Entity('canonical_addresses')
export class CanonicalAddress {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'house_number', nullable: true })
  houseNumber: string;

  @Column({ name: 'pre_directional', nullable: true })
  preDirectional: string;

  @Column({ name: 'street_name' })
  streetName: string;

  @Column({ name: 'street_suffix', nullable: true })
  streetSuffix: string;

  @Column({ name: 'post_directional', nullable: true })
  postDirectional: string;

  @Column({ name: 'unit_type', nullable: true })
  unitType: string;

  @Column({ name: 'unit_number', nullable: true })
  unitNumber: string;

  @Column({ nullable: true })
  city: string;

  @Column({ nullable: true })
  state: string;

  @Column({ name: 'state_abbr', length: 2, nullable: true })
  stateAbbr: string;

  @Column({ name: 'zip_code', nullable: true })
  zipCode: string;

  @Column({ name: 'zip_plus4', nullable: true })
  zipPlus4: string;

  @Column({ default: 'USA' })
  country: string;

  @Column({ name: 'full_address', type: 'text' })
  fullAddress: string;

  @Column({ name: 'normalized_key', type: 'text', unique: true })
  normalizedKey: string;

  @Column({ name: 'source_count', default: 1 })
  sourceCount: number;

  // embedding stored as raw text (pgvector managed via raw SQL)
  @Column({ type: 'text', nullable: true })
  embedding: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  @OneToMany(() => RawAddress, (r) => r.canonical)
  rawAddresses: RawAddress[];

  @OneToMany(() => StandardizationResult, (r) => r.canonical)
  standardizationResults: StandardizationResult[];
}
