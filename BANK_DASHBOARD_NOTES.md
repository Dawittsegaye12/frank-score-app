# Bank Dashboard Notes

## Features Delivered
- **Login/Auth**: Role-based access for `bank_admin`.
- **Borrower List**: Searchable, filterable list of applications with Risk Scores.
- **Detail View**: Comprehensive view with Score, Risk Band, Drivers, and Notes.
- **Drivers Logic**: Heuristic-based "Explainability" highlighting top strong/weak traits.
- **Portfolio**: Visual analytics using Chart.js.
- **Exports**: CSV export and Print-friendly PDF view.
- **Notes System**: Internal commenting system for loan officers.

## Known Limitations
- **PDF Export**: Relies on browser "Print to PDF" rather than server-side generation (simplified for MVP).
- **Drivers**: Uses simple raw trait score ranking rather than full SHAP values (as `shap` library wasn't available).
- **Auth**: Simple token-based auth stored in localStorage. Production should use HTTP-only cookies/JWT.

## Next Improvements
- **Advanced Filtering**: Add date range pickers.
- **Bulk Actions**: Select multiple borrowers to export or status update.
- **User Management**: Admin interface to create more bank users.
