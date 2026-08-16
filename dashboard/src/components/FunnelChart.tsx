interface FunnelChartProps {
    funnel: Record<string, number> | null
  }
  
  const FUNNEL_ORDER = ["page_view", "add_to_cart", "checkout_start", "checkout_complete"]
  
  const STEP_LABELS: Record<string, string> = {
    page_view: "Page view",
    add_to_cart: "Add to cart",
    checkout_start: "Checkout started",
    checkout_complete: "Checkout completed",
  }
  
  export default function FunnelChart({ funnel }: FunnelChartProps) {
    if (!funnel) {
      return <p className="text-sm text-neutral-500">Waiting for data...</p>
    }
  
    const steps = FUNNEL_ORDER.map((key) => ({
      key,
      label: STEP_LABELS[key],
      count: funnel[key] ?? 0,
    }))
  
    const maxCount = Math.max(...steps.map((s) => s.count), 1)
  
    return (
      <div className="space-y-3">
        <h2 className="text-sm font-medium text-neutral-300">
          Conversion funnel — current window
        </h2>
        {steps.map((step) => {
          const widthPct = (step.count / maxCount) * 100
          return (
            <div key={step.key} className="flex items-center gap-4">
              <span className="w-36 shrink-0 text-xs text-neutral-400">
                {step.label}
              </span>
              <div className="h-8 flex-1 rounded bg-neutral-900">
                <div
                  className="h-8 rounded bg-neutral-100 transition-all duration-500"
                  style={{ width: `${widthPct}%` }}
                />
              </div>
              <span className="w-10 shrink-0 text-right text-xs text-neutral-400">
                {step.count}
              </span>
            </div>
          )
        })}
      </div>
    )
  }