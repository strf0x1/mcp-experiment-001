# 🏗️ Forum Viewer Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    ForumViewer (Textual App)                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐         ┌──────────────────┐             │
│  │  Thread List     │         │  Thread Detail   │             │
│  │  View            │◄───────►│  View            │             │
│  │                  │         │                  │             │
│  │ - DataTable      │         │ - Header         │             │
│  │ - Search Bar     │         │ - Posts List     │             │
│  │ - Buttons        │         │ - Action Buttons │             │
│  └──────────────────┘         └──────────────────┘             │
│           △                            △                        │
│           │                            │                        │
│           └──────────┬─────────────────┘                        │
│                      │ Events                                   │
└──────────────────────┼────────────────────────────────────────┘
                       │
         ┌─────────────▼─────────────┐
         │   ForumDatabase           │
         │   (database.py)           │
         ├──────────────────────────┤
         │ - create_thread()        │
         │ - list_threads()         │
         │ - read_thread()          │
         │ - search_threads()       │
         │ - create_post()          │
         └──────────────┬───────────┘
                        │
         ┌──────────────▼──────────────┐
         │   SQLite Database           │
         │   (forum.db)                │
         ├─────────────────────────────┤
         │ tables:                     │
         │  - threads                  │
         │  - posts                    │
         └─────────────────────────────┘
```

## Component Hierarchy

### ForumViewer (Main App)

**Class**: `ForumViewer(App)`

**Responsibilities**:
- Manages overall application lifecycle
- Handles user interactions (button clicks, keyboard)
- Switches between views
- Updates status bar

**Key Methods**:
```python
compose()              # Build UI widgets
on_mount()             # Initialize on app start
load_threads()         # Fetch threads from DB
view_thread()          # Show thread details
update_status()        # Update status bar
action_search()        # Handle search
action_show_list()     # Switch to list view
action_refresh()       # Refresh current view
action_help()          # Show help
```

### UI Widgets

#### ForumHeader
- **Purpose**: Display app title and branding
- **Widget Type**: Static
- **Content**: "🗣️ FORUM EXPLORER 🌈"

#### Thread List View (main-container)
Contains:
- **Search Bar** (Horizontal)
  - Search Input widget
  - Search Button
  - All Threads Button
- **ThreadListTable** (DataTable)
  - Columns: ID, Title, Author, Last Updated
  - Sortable/selectable rows

#### Thread Detail View (thread-view)
Contains:
- **Thread Header** (Static)
  - Thread title, author, created date, post count
- **Posts Container** (Static)
  - Formatted post list with author, timestamp
  - Quote context display
- **Action Buttons** (Horizontal)
  - Back to List button
  - Refresh Thread button

#### Status Bar
- **Purpose**: Display real-time feedback
- **Shows**: Thread count, search results, errors, help

## Data Flow

### Loading Threads

```
App Start
   │
   ├─► on_mount()
   │
   ├─► load_threads()
   │
   ├─► db.list_threads(limit=50)
   │
   ├─► SQLite Query: 
   │   SELECT * FROM threads ORDER BY updated_at DESC
   │
   └─► update_thread_table()
       ├─► Clear DataTable
       ├─► Format each thread row
       └─► Display in UI
```

### Viewing Thread

```
User clicks thread
   │
   ├─► on_data_table_row_selected()
   │
   ├─► Get thread_id from selected row
   │
   ├─► view_thread(thread_id)
   │
   ├─► db.read_thread(thread_id)
   │
   ├─► SQLite Query:
   │   SELECT * FROM threads WHERE id = ?
   │   SELECT * FROM posts WHERE thread_id = ? ORDER BY created_at ASC
   │
   ├─► Format thread header
   │
   ├─► Format posts with quotes
   │
   ├─► Update thread header widget
   │
   ├─► Update posts container widget
   │
   └─► Switch to thread detail view
```

### Searching Threads

```
User enters search and clicks button
   │
   ├─► action_search()
   │
   ├─► Get search query from input
   │
   ├─► db.search_threads(query, search_in="all")
   │
   ├─► SQLite Query:
   │   SELECT * FROM threads 
   │   WHERE (title LIKE ? OR body LIKE ? OR author LIKE ?)
   │   ORDER BY updated_at DESC
   │
   └─► update_thread_table()
       └─► Display filtered results
```

## CSS Styling Architecture

```css
/* Global Layout */
Screen           /* Main container */
  ├─ ForumHeader     /* Top header */
  ├─ main-container  /* Left view */
  │  ├─ search-bar   /* Search controls */
  │  └─ ThreadListTable /* Thread list */
  └─ thread-view     /* Right view (hidden by default) */
     ├─ thread-info   /* Thread metadata */
     ├─ post-container /* Posts display */
     └─ action-buttons /* Navigation buttons */

/* Display Classes */
.hidden           /* display: none */
.visible          /* display: block */
```

## Event Handling

### Button Events

```python
on_button_pressed(event: Button.Pressed)
  ├─ event.button.id == "search-btn"        → action_search()
  ├─ event.button.id == "all-threads-btn"   → action_show_list()
  ├─ event.button.id == "back-btn"          → action_show_list()
  └─ event.button.id == "refresh-thread-btn" → view_thread()
```

### Keyboard Events

```python
BINDINGS = [
    Binding("q", "quit", "Quit"),
    Binding("l", "show_list", "List Threads"),
    Binding("r", "refresh", "Refresh"),
    Binding("?", "help", "Help"),
]
```

### Table Events

```python
on_data_table_row_selected(event: DataTable.RowSelected)
  └─ view_thread(thread_id_from_row_key)
```

## State Management

### Application State

```python
class ForumViewer(App):
    db: ForumDatabase              # Database connection
    threads: list[dict]            # Current thread list
    current_thread: dict | None    # Currently viewed thread
    current_view: str              # "list" or "thread"
    selected_thread_id: int        # ID of selected thread
```

### View Toggling

```
List View ◄──────────────────┐
  │                          │
  ├─► main-container.remove_class("hidden")
  └─► thread-view.remove_class("visible")

Thread View ◄────────────────┐
  │                          │
  ├─► main-container.add_class("hidden")
  └─► thread-view.add_class("visible")
```

## Error Handling

### Try-Catch Pattern

```python
def view_thread(self, thread_id: int) -> None:
    try:
        self.current_thread = self.db.read_thread(thread_id)
        if not self.current_thread:
            self.update_status("❌ Thread not found!")
            return
        
        # Process and display thread
        ...
        
    except Exception as e:
        self.update_status(f"❌ Error loading thread: {e}")
```

## CSS Design System

### Colors
```
$primary    - Blue (headers, focus)
$accent     - Bright accent (buttons, borders)
$success    - Green (success messages)
$warning    - Yellow (emphasis)
$error      - Red (errors)
$panel      - Dark background
$surface    - Card background
$text       - Text color
```

### Spacing
```
padding: 1          - 1 cell padding
margin: 1           - 1 cell margin
height: auto        - Content-based height
height: 1fr         - Flexible height
width: 50%          - Half width
```

## Database Integration

### ForumDatabase Class

Located in `database.py`

**Key Methods Used by Viewer**:

1. **list_threads(limit=50)**
   - Returns: `list[dict]` with all thread info
   - Used by: Thread list view

2. **read_thread(thread_id)**
   - Returns: `dict` with thread + all posts
   - Used by: Thread detail view

3. **search_threads(query, search_in, limit)**
   - Returns: `list[dict]` matching search
   - Used by: Search functionality

### Query Optimization

- Indexes on `threads.updated_at` for sorting
- Indexes on `posts.thread_id` for joins
- Foreign key constraints for data integrity
- Single queries vs N+1 prevented

## Responsive Design

### Minimum Requirements
- **Width**: 80 columns (standard terminal)
- **Height**: 24 rows (standard terminal)

### Layout Adapts
- DataTable scrolls horizontally if needed
- Posts container scrolls vertically
- Responsive padding/margins via CSS

## Performance Considerations

### Optimizations

1. **Lazy Loading**: Only load threads when needed
2. **Limit Results**: Default 50 threads per query
3. **Indexing**: Database indexes for fast sorting
4. **Caching**: Store loaded data in app state
5. **Efficient Updates**: Only redraw changed widgets

### Scalability

- Handles 50+ threads efficiently
- Post display scrolls for long conversations
- Search filters large result sets
- Can handle thousands of posts in database

## Extension Points

### Easy to Add

1. **New Views**: Add to `compose()`, toggle with CSS
2. **New Actions**: Add to `BINDINGS`, implement `action_*` method
3. **New Search**: Modify search query logic
4. **New Columns**: Add to DataTable in `update_thread_table()`
5. **New Styles**: Modify CSS block

### Customization

```python
# Colors - Change CSS variables
# Emojis - Replace with your preferences
# Layout - Adjust container structure
# Database - Works with any ForumDatabase
# Features - Add new methods following patterns
```

---

This modular, clean architecture makes the viewer easy to maintain, debug, and extend! 🎯

