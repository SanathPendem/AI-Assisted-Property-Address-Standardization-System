import { Controller, Get, Query, Logger } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { AuditService } from './audit.service';
import { AuditFilterDto } from '../common/dto';

@ApiTags('audit')
@Controller('audit')
export class AuditController {
  private readonly logger = new Logger(AuditController.name);

  constructor(private readonly auditService: AuditService) {}

  @Get()
  @ApiOperation({ summary: 'Query the immutable audit trail with filters' })
  @ApiResponse({ status: 200, description: 'Filtered audit trail' })
  async getAuditTrail(@Query() filter: AuditFilterDto) {
    return this.auditService.getAuditTrail(filter);
  }
}
