import { Controller, Get, Post, Param, Body, Query, Logger } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiQuery } from '@nestjs/swagger';
import { ReviewService } from './review.service';
import { ReviewDecisionDto } from '../common/dto';
import { PaginationDto } from '../common/dto';

@ApiTags('review')
@Controller('review')
export class ReviewController {
  private readonly logger = new Logger(ReviewController.name);

  constructor(private readonly reviewService: ReviewService) {}

  @Get('queue')
  @ApiOperation({
    summary: 'Get items pending human review',
    description: 'Returns review queue items sorted by priority score (highest first). Supports pagination.',
  })
  @ApiQuery({ name: 'status', required: false, example: 'pending', description: 'Filter by review status' })
  @ApiResponse({
    status: 200,
    description: 'Paginated review queue',
    schema: {
      example: {
        items: [
          {
            id: 'uuid',
            rawAddressText: '45 W 34 St Apt 2, NY 12308',
            predictedAddress: '45 West 34th Street, Apartment 2, New York, NY 12308',
            confidenceScore: 0.67,
            routingDecision: 'pending_review',
            priorityScore: 0.98,
            reviewStatus: 'pending',
            contextNotes: 'Medium confidence match...',
          },
        ],
        total: 42,
        page: 1,
        limit: 20,
      },
    },
  })
  async getQueue(
    @Query() pagination: PaginationDto,
    @Query('status') status?: string,
  ) {
    return this.reviewService.getQueue(pagination, status);
  }

  @Post(':id/decide')
  @ApiOperation({
    summary: 'Submit a human decision for a queue item',
    description: 'Accept, correct, or reject the prediction. Triggers canonicalization if accepted/corrected.',
  })
  async decide(
    @Param('id') id: string,
    @Body() dto: ReviewDecisionDto,
  ) {
    this.logger.log(`Review decision for ${id}: ${dto.decision}`);
    return this.reviewService.decide(id, dto);
  }
}
