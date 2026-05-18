import PageHeader from '@/components/PageHeader'
import { Card, CardContent } from '@/components/ui'

export default function PlaceholderPage({ title, note }: { title: string; note: string }) {
  return (
    <div>
      <PageHeader title={title} />
      <div className="p-8">
        <Card>
          <CardContent>
            <p className="text-slate-600">{note}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
