import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsNotEmpty, IsOptional, IsString } from 'class-validator';

export class StandardizeAddressDto {
  @ApiProperty({ example: '45 W 34 St Apt 2, NY 12308', description: 'Raw address string to standardize' })
  @IsNotEmpty()
  @IsString()
  rawAddress: string;

  @ApiPropertyOptional({ example: 'property_db', description: 'Source system identifier' })
  @IsOptional()
  @IsString()
  sourceSystem?: string;

  @ApiPropertyOptional({ example: 'REC-12345', description: 'Source record ID for traceability' })
  @IsOptional()
  @IsString()
  sourceRecordId?: string;
}
