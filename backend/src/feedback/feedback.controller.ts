import { Controller, Get, Query, Logger } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse } from '@nestjs/swagger';
import { FeedbackService } from './feedback.service';
import { PaginationDto } from '../common/dto';

@ApiTags('feedback')
@Controller('feedback')
export class FeedbackController {
  private readonly logger = new Logger(FeedbackController.name);

  constructor(private readonly feedbackService: FeedbackService) {}

  @Get()
  @ApiOperation({ summary: 'Get accumulated feedback items' })
  @ApiResponse({ status: 200, description: 'List of feedback items' })
  async getFeedback(@Query() pagination: PaginationDto) {
    return this.feedbackService.getFeedback(pagination);
  }
}
