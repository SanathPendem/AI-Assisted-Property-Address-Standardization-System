import { NestFactory } from '@nestjs/core';
import { ValidationPipe } from '@nestjs/common';
import { SwaggerModule, DocumentBuilder } from '@nestjs/swagger';
import { NestExpressApplication } from '@nestjs/platform-express';
import { join } from 'path';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create<NestExpressApplication>(AppModule);

  // ── Serve static frontend assets ──────────────────────────────────────────
  app.useStaticAssets(join(__dirname, '..', 'public'));

  // ── Global validation pipe ──────────────────────────────────────────────────
  app.useGlobalPipes(
    new ValidationPipe({
      whitelist: true,
      forbidNonWhitelisted: true,
      transform: true,
      transformOptions: { enableImplicitConversion: true },
    }),
  );

  // ── CORS ───────────────────────────────────────────────────────────────────
  app.enableCors({ origin: '*' });

  // ── Swagger / OpenAPI ──────────────────────────────────────────────────────
  const config = new DocumentBuilder()
    .setTitle('Address Standardization API')
    .setDescription(
      'Production-grade AI-assisted address standardization system with human-in-the-loop validation.',
    )
    .setVersion('1.0')
    .addTag('addresses', 'Address ingestion and standardization')
    .addTag('review', 'Human review queue management')
    .addTag('feedback', 'Human feedback and corrections')
    .addTag('audit', 'Audit trail and history')
    .addTag('ml', 'ML model management and retraining')
    .build();

  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('api/docs', app, document);

  const port = process.env.PORT ?? 3000;
  await app.listen(port);
  console.log(`🚀 Web Dashboard running at http://localhost:${port}`);
  console.log(`📚 Swagger docs at http://localhost:${port}/api/docs`);
}

bootstrap();
