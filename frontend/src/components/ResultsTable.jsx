export default function ResultsTable({ assignments }) {
  return (
    <div className="overflow-hidden rounded-lg border border-line">
      <table className="w-full font-body text-sm">
        <thead>
          <tr className="bg-ink text-paper">
            <th className="px-4 py-3 text-right font-medium">درس</th>
            <th className="px-4 py-3 text-right font-medium">استاد</th>
            <th className="px-4 py-3 text-right font-medium">کلاس</th>
            <th className="px-4 py-3 text-right font-medium">روز</th>
            <th className="px-4 py-3 text-right font-medium">ساعت</th>
          </tr>
        </thead>
        <tbody>
          {assignments.map((a, i) => (
            <tr key={i} className={i % 2 === 0 ? "bg-white/60" : "bg-paper"}>
              <td className="px-4 py-3">{a.course_name}</td>
              <td className="px-4 py-3">{a.professor_last_name}</td>
              <td className="px-4 py-3">{a.classroom_name}</td>
              <td className="px-4 py-3">{a.day}</td>
              <td className="px-4 py-3 font-mono text-primary">
                {a.start_time}–{a.end_time}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
