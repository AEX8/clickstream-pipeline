interface Stat {
    label: string
    value: string
  }
  
  const STATS: Stat[] = [
    { label: "Active users", value: "—" },
    { label: "Events / min", value: "—" },
    { label: "Conversion rate", value: "—" },
  ]
  
  export default function StatStrip() {
    return (
      <div className="grid grid-cols-3 divide-x divide-neutral-800 border-b border-neutral-800">
        {STATS.map((stat) => (
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