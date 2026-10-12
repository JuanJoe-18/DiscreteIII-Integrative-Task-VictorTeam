import type { ReactNode } from 'react'
import Icon from './Icon'

export function Card({ children, className = '', as: As = 'section', ...rest }: { children: ReactNode; className?: string; as?: 'section' | 'div' | 'article' | 'aside'; 'aria-labelledby'?: string; 'aria-label'?: string }) {
  return (
    <As className={`rounded-lg border border-[#e0dfdc] bg-white shadow-[0_0_0_1px_rgba(0,0,0,0.02),0_1px_2px_rgba(0,0,0,0.06)] ${className}`} {...rest}>
      {children}
    </As>
  )
}

export function Chip({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'blue' | 'warn' }) {
  const t = { neutral: 'border-[#c9c8c5] text-[#404040] bg-white', blue: 'border-[#0a66c2]/40 text-[#004182] bg-[#eaf3fc]', warn: 'border-[#b24020]/40 text-[#8f2f12] bg-[#fdf1ec]' }[tone]
  return <span className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-[13px] font-medium ${t}`}>{children}</span>
}

export function StatusBadge({ accepted }: { accepted: boolean }) {
  return accepted ? (
    <span className="inline-flex items-center gap-1 rounded-full bg-[#e6f4ea] px-2.5 py-1 text-[13px] font-semibold text-[#0b6b2e]">
      <Icon name="check" className="size-4" /> Pattern satisfied
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 rounded-full bg-[#f3f2ef] px-2.5 py-1 text-[13px] font-semibold text-[#5e5e5e] ring-1 ring-[#c9c8c5]">
      <Icon name="x" className="size-4" /> Pattern not satisfied
    </span>
  )
}

export function Button({ variant = 'primary', className = '', ...p }: React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'ghost' }) {
  const v = {
    primary: 'bg-[#0a66c2] text-white hover:bg-[#004182] disabled:bg-[#a8c6e5]',
    secondary: 'bg-white text-[#0a66c2] ring-1 ring-inset ring-[#0a66c2] hover:bg-[#eaf3fc] hover:ring-2',
    ghost: 'text-[#5e5e5e] hover:bg-[#ebebeb] hover:text-[#1d1d1d]',
  }[variant]
  return <button className={`inline-flex items-center justify-center gap-1.5 rounded-full px-4 py-1.5 text-[15px] font-semibold transition ${v} ${className}`} {...p} />
}

export function EngineNotice({ className = '' }: { className?: string }) {
  return (
    <p className={`inline-flex items-center gap-1.5 rounded-md bg-[#eaf3fc] px-2.5 py-1 text-[12px] font-medium text-[#004182] ${className}`}>
      <Icon name="info" className="size-3.5" /> Real engine · Python + pyformlang
    </p>
  )
}

export function SectionTitle({ id, children, sub }: { id?: string; children: ReactNode; sub?: ReactNode }) {
  return (
    <div>
      <h2 id={id} className="text-[18px] font-semibold text-[#1d1d1d]">{children}</h2>
      {sub && <p className="mt-0.5 text-[14px] text-[#666]">{sub}</p>}
    </div>
  )
}
