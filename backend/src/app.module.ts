import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { WinstonModule } from 'nest-winston';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { winstonConfig } from './common/logging/winston.config';
import { DatabaseModule } from './database/database.module';
import { PlannerModule } from './modules/planner/planner.module';
import { ConceptModule } from './modules/concept/concept.module';
import { AssessmentModule } from './modules/assessment/assessment.module';
import { AnalyticsModule } from './modules/analytics/analytics.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    WinstonModule.forRoot(winstonConfig),
    DatabaseModule,
    PlannerModule,
    ConceptModule,
    AssessmentModule,
    AnalyticsModule,
  ],
  controllers: [AppController],
  providers: [AppService],
})
export class AppModule {}
