import React from 'react';
import { Outlet } from 'react-router-dom';
import Header from './Header/header.jsx';

function Layout() {
    return (
        <>
            <Header />
            <main className="flex-1 p-8 min-h-[calc(100vh-64px)]">
                <Outlet />
            </main>
        </>
    );
}

export default Layout;

