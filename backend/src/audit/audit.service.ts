import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { AuditTrail } from '../database/entities/audit-trail.entity';
import { AuditFilterDto } from '../common/dto';

@Injectable()
export class AuditService {
  private readonly logger = new Logger(AuditService.name);

  constructor(
    @InjectRepository(AuditTrail)
    private readonly auditRepo: Repository<AuditTrail>,
  ) {}

  async getAuditTrail(filter: AuditFilterDto) {
    const { page, limit, eventType, startDate, endDate } = filter;

    const query = this.auditRepo.createQueryBuilder('a')
      .leftJoinAndSelect('a.rawAddress', 'rawAddress')
      .orderBy('a.createdAt', 'DESC');

    if (eventType) {
      query.andWhere('a.eventType = :eventType', { eventType });
    }

    if (startDate) {
      query.andWhere('a.createdAt >= :startDate', { startDate });
    }

    if (endDate) {
      query.andWhere('a.createdAt <= :endDate', { endDate });
    }

    const [items, total] = await query
      .skip((page - 1) * limit)
      .take(limit)
      .getManyAndCount();

    return {
      items,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit),
    };
  }
}
