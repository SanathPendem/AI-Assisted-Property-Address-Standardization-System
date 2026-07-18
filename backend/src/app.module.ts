import { Module } from '@nestjs/common';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { TypeOrmModule } from '@nestjs/typeorm';
import { BullModule } from '@nestjs/bull';
import { HttpModule } from '@nestjs/axios';

import { AddressesModule } from './addresses/addresses.module';
import { ReviewModule } from './review/review.module';
import { FeedbackModule } from './feedback/feedback.module';
import { AuditModule } from './audit/audit.module';
import { MlModule } from './ml/ml.module';
import { HealthModule } from './health/health.module';

import { RawAddress } from './database/entities/raw-address.entity';
import { CanonicalAddress } from './database/entities/canonical-address.entity';
import { StandardizationResult } from './database/entities/standardization-result.entity';
import { ReviewQueue } from './database/entities/review-queue.entity';
import { Feedback } from './database/entities/feedback.entity';
import { AuditTrail } from './database/entities/audit-trail.entity';
import { ModelRegistry } from './database/entities/model-registry.entity';

@Module({
  imports: [
    // ── Config ──────────────────────────────────────────────────────────────
    ConfigModule.forRoot({ isGlobal: true, envFilePath: '.env' }),

    // ── Database ────────────────────────────────────────────────────────────
    TypeOrmModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (config: ConfigService) => ({
        type: 'postgres',
        host: config.get('DATABASE_HOST', 'localhost'),
        port: parseInt(config.get('DATABASE_PORT', '5432')),
        username: config.get('DATABASE_USER', 'addruser'),
        password: config.get('DATABASE_PASSWORD', 'addrpass'),
        database: config.get('DATABASE_NAME', 'address_db'),
        entities: [
          RawAddress,
          CanonicalAddress,
          StandardizationResult,
          ReviewQueue,
          Feedback,
          AuditTrail,
          ModelRegistry,
        ],
        synchronize: false, // use migrations
        logging: config.get('NODE_ENV') === 'development',
      }),
      inject: [ConfigService],
    }),

    // ── Redis / Bull ────────────────────────────────────────────────────────
    BullModule.forRootAsync({
      imports: [ConfigModule],
      useFactory: (config: ConfigService) => ({
        redis: {
          host: config.get('REDIS_HOST', 'localhost'),
          port: parseInt(config.get('REDIS_PORT', '6379')),
        },
      }),
      inject: [ConfigService],
    }),

    // ── HTTP Client ─────────────────────────────────────────────────────────
    HttpModule.register({ timeout: 30000 }),

    // ── Feature Modules ─────────────────────────────────────────────────────
    AddressesModule,
    ReviewModule,
    FeedbackModule,
    AuditModule,
    MlModule,
    HealthModule,
  ],
})
export class AppModule {}
