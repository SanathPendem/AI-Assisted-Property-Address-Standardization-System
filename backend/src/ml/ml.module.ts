import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { ModelRegistry } from '../database/entities/model-registry.entity';
import { Feedback } from '../database/entities/feedback.entity';
import { AuditTrail } from '../database/entities/audit-trail.entity';
import { MlClientService } from './ml-client.service';
import { MlController } from './ml.controller';
import { MlService } from './ml.service';

@Module({
  imports: [TypeOrmModule.forFeature([ModelRegistry, Feedback, AuditTrail])],
  controllers: [MlController],
  providers: [MlClientService, MlService],
  exports: [MlClientService, MlService],
})
export class MlModule {}
