'use client';

import React from 'react';

interface ScoreRingProps {
  score: number;
  size?: number;
  strokeWidth?: number;
  label?: string;
  sublabel?: string;
}

export default function ScoreRing({
  score,
  size = 104,
  strokeWidth = 8,
  label = 'Score Global de PI & LOPDP',
  sublabel = 'Cumplimiento Certificado',
}: ScoreRingProps) {
  const center = size / 2;
  const radius = center - strokeWidth;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.min(Math.max(score, 0), 100);
  const strokeDashoffset = circumference - (clampedScore / 100) * circumference;

  return (
    <div className='flex items-center space-x-4 bg-white dark:bg-[#141417] border border-zinc-200 dark:border-[#26262b] rounded-xl p-4 shadow-sm dark:shadow-lg transition-colors'>
      <div className='relative shrink-0' style={{ width: size, height: size }}>
        <svg width={size} height={size} className='transform -rotate-90'>
          <defs>
            <linearGradient id='aiGradientScore' x1='0%' y1='0%' x2='100%' y2='100%'>
              <stop offset='0%' stopColor='#9a3bf1' />
              <stop offset='100%' stopColor='#3892f3' />
            </linearGradient>
          </defs>
          <circle
            cx={center}
            cy={center}
            r={radius}
            strokeWidth={strokeWidth}
            fill='transparent'
            className='stroke-zinc-200 dark:stroke-[#26262b] transition-colors'
          />
          <circle
            cx={center}
            cy={center}
            r={radius}
            stroke='url(#aiGradientScore)'
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap='round'
            fill='transparent'
            className='transition-all duration-1000 ease-out'
          />
        </svg>

        <div className='absolute inset-0 flex flex-col items-center justify-center'>
          <span className='text-2xl font-extrabold tracking-tight text-zinc-900 dark:text-white font-mono'>
            {clampedScore}%
          </span>
          <span className='text-[10px] uppercase font-semibold text-zinc-500 dark:text-zinc-400 tracking-wider'>
            Índice
          </span>
        </div>
      </div>

      <div className='flex flex-col'>
        <div className='flex items-center space-x-2'>
          <span className='inline-block w-2 h-2 rounded-full bg-[#00c853] animate-pulse' />
          <h4 className='text-sm font-bold text-zinc-900 dark:text-white tracking-tight'>{label}</h4>
        </div>
        <p className='text-xs text-zinc-600 dark:text-zinc-400 mt-1 max-w-[200px] leading-relaxed'>
          {sublabel}
        </p>
        <div className='mt-2.5 flex items-center space-x-2'>
          <span className='badge-render-success text-[10px] font-bold px-2 py-0.5 rounded-full uppercase tracking-wider'>
            {clampedScore >= 80 ? 'Nivel Óptimo' : clampedScore >= 50 ? 'En Riesgo' : 'Crítico'}
          </span>
          <span className='text-[11px] text-zinc-500 dark:text-zinc-400 font-mono'>ADPA 360</span>
        </div>
      </div>
    </div>
  );
}
