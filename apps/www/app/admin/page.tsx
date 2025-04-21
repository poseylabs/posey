import Link from 'next/link';

export default function AdminDashboardPage() {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-8">Admin Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Card for Minions */}
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">Minions</h2>
            <p>Manage and configure specialized AI agents (Minions).</p>
            <div className="card-actions justify-end">
              <Link href="/admin/minions" className="btn btn-primary">Go to Minions</Link>
            </div>
          </div>
        </div>

        {/* Card for Models */}
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">LLM Models</h2>
            <p>Manage Large Language Models available in the system.</p>
            <div className="card-actions justify-end">
              <Link href="/admin/models" className="btn btn-primary">Go to Models</Link>
            </div>
          </div>
        </div>

        {/* Card for Providers */}
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">LLM Providers</h2>
            <p>Manage LLM API providers and their configurations.</p>
            <div className="card-actions justify-end">
              <Link href="/admin/providers" className="btn btn-primary">Go to Providers</Link>
            </div>
          </div>
        </div>

        {/* Card for Invites */}
        <div className="card bg-base-100 shadow-xl">
          <div className="card-body">
            <h2 className="card-title">Invites</h2>
            <p>Manage user invitation codes.</p>
            <div className="card-actions justify-end">
              <Link href="/admin/invites" className="btn btn-primary">Go to Invites</Link>
            </div>
          </div>
        </div>

        {/* Add more cards here for future admin pages */}

      </div>
    </div>
  );
}
