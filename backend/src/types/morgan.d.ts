declare module 'morgan' {
  import type { Handler } from 'express';

  export default function morgan(format: string): Handler;
}
