import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { RawAddress } from '../database/entities/raw-address.entity';
import { CanonicalAddress } from '../database/entities/canonical-address.entity';
import { StandardizationResult } from '../database/entities/standardization-result.entity';
import { ReviewQueue } from '../database/entities/review-queue.entity';
import { AuditTrail } from '../database/entities/audit-trail.entity';
import { MlModule } from '../ml/ml.module';
import { AddressesController } from './addresses.controller';
import { AddressesService } from './addresses.service';

@Module({
  imports: [
    TypeOrmModule.forFeature([
      RawAddress,
      CanonicalAddress,
      StandardizationResult,
      ReviewQueue,
      AuditTrail,
    ]),
    MlModule,
  ],
  controllers: [AddressesController],
  providers: [AddressesService],
  exports: [AddressesService],
})
export class AddressesModule {}
