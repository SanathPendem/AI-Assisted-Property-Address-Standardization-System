import { Controller, Post, Get, Logger } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { MlService } from './ml.service';

@ApiTags('ml')
@Controller('ml')
export class MlController {
  private readonly logger = new Logger(MlController.name);

  constructor(private readonly mlService: MlService) {}

  @Post('retrain')
  @ApiOperation({ summary: 'Trigger model retraining with accumulated feedback' })
  @ApiResponse({ status: 200, description: 'Retraining completed successfully' })
  @ApiResponse({ status: 503, description: 'ML service unavailable' })
  async triggerRetrain() {
    this.logger.log('Manual retrain triggered');
    return this.mlService.triggerRetrain();
  }

  @Get('status')
  @ApiOperation({ summary: 'Get current model metadata and accuracy metrics' })
  @ApiResponse({ status: 200, description: 'Model status retrieved' })
  async getStatus() {
    return this.mlService.getModelStatus();
  }
}
