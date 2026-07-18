import { Injectable, Logger, HttpException, HttpStatus } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';
import axios, { AxiosInstance } from 'axios';

export interface MlStandardizeResponse {
  standardized_address: string;
  confidence_score: number;
  parsed_components: Record<string, string>;
  feature_vector: Record<string, number>;
  model_version: string;
  processing_time_ms: number;
  canonical_components: {
    house_number: string;
    pre_directional: string;
    street_name: string;
    street_suffix: string;
    post_directional: string;
    unit_type: string;
    unit_number: string;
    city: string;
    state: string;
    state_abbr: string;
    zip_code: string;
  };
}

export interface MlRetrainResponse {
  status: string;
  model_version: string;
  metrics: {
    accuracy: number;
    precision: number;
    recall: number;
    f1: number;
    training_samples: number;
  };
}

@Injectable()
export class MlClientService {
  private readonly logger = new Logger(MlClientService.name);
  private readonly client: AxiosInstance;

  constructor(private config: ConfigService) {
    const baseURL = config.get('ML_SERVICE_URL', 'http://localhost:8000');
    this.client = axios.create({ baseURL, timeout: 30000 });
    this.logger.log(`ML Service client configured: ${baseURL}`);
  }

  async standardize(rawAddress: string): Promise<MlStandardizeResponse> {
    try {
      const { data } = await this.client.post('/standardize', { raw_address: rawAddress });
      return data;
    } catch (error) {
      this.logger.error(`ML standardize failed: ${error.message}`);
      throw new HttpException(
        'ML service unavailable or returned error',
        HttpStatus.SERVICE_UNAVAILABLE,
      );
    }
  }

  async triggerRetrain(feedbackData: any[]): Promise<MlRetrainResponse> {
    try {
      const { data } = await this.client.post('/retrain', { feedback: feedbackData });
      return data;
    } catch (error) {
      this.logger.error(`ML retrain failed: ${error.message}`);
      throw new HttpException(
        'ML service retrain failed',
        HttpStatus.SERVICE_UNAVAILABLE,
      );
    }
  }

  async getModelMetrics(): Promise<any> {
    try {
      const { data } = await this.client.get('/model/metrics');
      return data;
    } catch (error) {
      this.logger.error(`ML metrics fetch failed: ${error.message}`);
      throw new HttpException('ML service unavailable', HttpStatus.SERVICE_UNAVAILABLE);
    }
  }

  async getEmbedding(address: string): Promise<number[]> {
    try {
      const { data } = await this.client.post('/embed', { address });
      return data.embedding;
    } catch (error) {
      this.logger.error(`ML embed failed: ${error.message}`);
      return [];
    }
  }
}
