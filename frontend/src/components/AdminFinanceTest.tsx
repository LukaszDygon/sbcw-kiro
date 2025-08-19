/**
 * Test component to verify AdminPanel and Reports components
 */
import React from 'react'
import AdminPanel from './AdminPanel'
import Reports from './Reports'

const AdminFinanceTest: React.FC = () => {
  const mockUser = {
    id: 'test-user-id',
    role: 'ADMIN'
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-8">Admin & Finance Components Test</h1>
      
      <div className="mb-12">
        <h2 className="text-xl font-semibold mb-4">Admin Panel</h2>
        <AdminPanel currentUser={mockUser} />
      </div>
      
      <div>
        <h2 className="text-xl font-semibold mb-4">Finance Reports</h2>
        <Reports currentUser={mockUser} />
      </div>
    </div>
  )
}

export default AdminFinanceTest