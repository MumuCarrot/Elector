import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header/header.jsx';

/**
 * Main chrome: site header and an `<Outlet />` for nested routes.
 *
 * @returns {JSX.Element} Layout fragment.
 */
function Layout() {
    return (
        <>
            <Header />
            <main className="content-center p-8 min-h-[calc(100vh-65px)]">
                <Outlet />
            </main>
        </>
    );
}

export default Layout;

