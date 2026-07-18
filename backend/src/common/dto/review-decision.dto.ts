import { ApiProperty, ApiPropertyOptional } from '@nestjs/swagger';
import { IsEnum, IsNotEmpty, IsOptional, IsString } from 'class-validator';

export enum HumanDecision {
  ACCEPTED = 'accepted',
  CORRECTED = 'corrected',
  REJECTED = 'rejected',
}

export class ReviewDecisionDto {
  @ApiProperty({ enum: HumanDecision, example: 'corrected' })
  @IsEnum(HumanDecision)
  decision: HumanDecision;

  @ApiPropertyOptional({ example: '45 West 34th Street, Apartment 2, New York, NY 12308', description: 'Corrected address (required when decision=corrected)' })
  @IsOptional()
  @IsString()
  correctedAddress?: string;

  @ApiProperty({ example: 'reviewer-001', description: 'Reviewer identifier' })
  @IsNotEmpty()
  @IsString()
  reviewerId: string;

  @ApiPropertyOptional({ example: 'Street name was abbreviated incorrectly', description: 'Reason for the decision' })
  @IsOptional()
  @IsString()
  rationale?: string;
}
