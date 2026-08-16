interface StatStripProps {
    activeUsers: number | null
    eventsPerWindow: number | null
    conversionRate: string | null
  }
  
  export default function StatStrip({ activeUsers, eventsPerWindow, conversionRate }: StatStripProps) {
    const stats = [
      { label: "Active users", value: activeUsers?.toString() ?? "—" },
      { label: "Events / window", value: eventsPerWindow?.toString() ?? "—" },
      { label: "Conversion rate", value: conversionRate ?? "—" },
    ]
  
    return (
      <div className="grid grid-cols-3 divide-x divide-neutral-800 border-b border-neutral-800">
        {stats.map((stat) => (
          <div key={stat.label} className="px-6 py-5">
            <p className="text-xs font-medium uppercase tracking-wide text-neutral-500">
              {stat.label}
            </p>
            <p className="mt-1 text-2xl font-semibold text-neutral-100">
              {stat.value}
            </p>
          </div>
        ))}
      </div>
    )
  }