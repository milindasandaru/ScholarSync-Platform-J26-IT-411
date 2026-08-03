import { NestFactory } from '@nestjs/core';
import morgan from 'morgan';
import { AppModule } from './app.module';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  app.enableCors({
    origin: process.env.FRONTEND_URL ?? 'http://localhost:3000',
    credentials: true,
  });
  app.setGlobalPrefix('api');
  app.use(morgan(process.env.NODE_ENV === 'production' ? 'combined' : 'dev'));

  await app.listen(process.env.PORT ?? 3001);
}
void bootstrap();
