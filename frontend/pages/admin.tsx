import type { NextPage } from 'next'
import Head from 'next/head'
import AdminDashboardHome from '../components/storefront/AdminDashboardHome'

const AdminPage: NextPage = () => {
  return (
    <>
      <Head>
        <title>Miracle Coins Admin</title>
        <meta name="description" content="Admin dashboard for Miracle Coins inventory management" />
      </Head>
      <AdminDashboardHome />
    </>
  )
}

export default AdminPage
