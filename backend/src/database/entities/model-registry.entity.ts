import {
  Entity, PrimaryGeneratedColumn, Column, CreateDateColumn,
} from 'typeorm';

@Entity('model_registry')
export class ModelRegistry {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ unique: true })
  version: string;

  @Column({ name: 'artifact_path', type: 'text' })
  artifactPath: string;

  @Column({ name: 'training_samples', nullable: true })
  trainingSamples: number;

  @Column({ type: 'numeric', precision: 5, scale: 4, nullable: true })
  accuracy: number;

  @Column({ name: 'precision_score', type: 'numeric', precision: 5, scale: 4, nullable: true })
  precisionScore: number;

  @Column({ name: 'recall_score', type: 'numeric', precision: 5, scale: 4, nullable: true })
  recallScore: number;

  @Column({ name: 'f1_score', type: 'numeric', precision: 5, scale: 4, nullable: true })
  f1Score: number;

  @Column({ name: 'training_log', type: 'jsonb', nullable: true })
  trainingLog: Record<string, any>;

  @Column({ name: 'is_active', default: false })
  isActive: boolean;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;
}
