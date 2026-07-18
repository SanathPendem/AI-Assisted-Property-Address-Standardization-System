import { Controller, Post, Get, Param, Query, Body, Logger } from '@nestjs/common';
import { ApiTags, ApiOperation, ApiResponse, ApiBody } from '@nestjs/swagger';
import { AddressesService } from './addresses.service';
import { StandardizeAddressDto, PaginationDto } from '../common/dto';

@ApiTags('addresses')
@Controller('addresses')
export class AddressesController {
  private readonly logger = new Logger(AddressesController.name);

  constructor(private readonly addressesService: AddressesService) {}

  @Post('standardize')
  @ApiOperation({
    summary: 'Standardize a raw property address',
    description: 'Accepts a raw address string, runs it through the ML pipeline, assigns a confidence score, and routes it based on confidence thresholds.',
  })
  @ApiBody({ type: StandardizeAddressDto })
  @ApiResponse({
    status: 201,
    description: 'Address standardized successfully',
    schema: {
      example: {
        id: 'uuid',
        rawAddress: '45 W 34 St Apt 2, NY 12308',
        standardizedAddress: '45 West 34th Street, Apartment 2, New York, NY 12308',
        confidenceScore: 0.87,
        routingDecision: 'auto_accepted',
        parsedComponents: { house_number: '45', road: 'West 34th Street', unit: 'Apartment 2', city: 'New York', state: 'NY', postcode: '12308' },
      },
    },
  })
  async standardize(@Body() dto: StandardizeAddressDto) {
    this.logger.log(`Standardize request: ${dto.rawAddress}`);
    return this.addressesService.standardize(dto);
  }

  @Get()
  @ApiOperation({ summary: 'List all standardized addresses (paginated)' })
  @ApiResponse({ status: 200, description: 'Paginated list of standardization results' })
  async findAll(@Query() pagination: PaginationDto) {
    return this.addressesService.findAll(pagination);
  }

  @Get(':id')
  @ApiOperation({ summary: 'Get a standardization result by ID' })
  @ApiResponse({ status: 200, description: 'Standardization result found' })
  @ApiResponse({ status: 404, description: 'Not found' })
  async findOne(@Param('id') id: string) {
    return this.addressesService.findOne(id);
  }
}
