import { useState } from "react";

export interface TodoItem {
  id: string;
  assignee: string;
  actionItem: string;
  deadline: string;
  completed?: boolean;
}

interface TodoListProps {
  todoItems: TodoItem[];
}

export default function TodoList({ todoItems }: TodoListProps) {
  const [items, setItems] = useState(todoItems);

  const toggleComplete = (id: string) => {
    setItems(
      items.map((item) =>
        item.id === id ? { ...item, completed: !item.completed } : item
      )
    );
  };

  return (
    <div className="bg-white rounded-lg border border-gray-300 p-6">
      <h2 className="text-xl font-bold text-gray-800 mb-6">할 일 목록</h2>

      <div className="space-y-4">
        <div className="grid grid-cols-[auto_1fr_minmax(60px,80px)_minmax(80px,120px)] gap-4 pb-2 border-b border-gray-200 text-sm font-medium text-gray-600">
          <div></div>
          <div>할 일</div>
          <div>담당자</div>
          <div>기한</div>
        </div>

        {items.map((item) => (
          <div
            key={item.id}
            className={`grid grid-cols-[auto_1fr_minmax(60px,80px)_minmax(80px,120px)] gap-4 items-center py-2 ${
              item.completed ? "line-through text-gray-500" : "text-gray-900"
            }`}
          >
            <input
              type="checkbox"
              checked={item.completed || false}
              onChange={() => toggleComplete(item.id)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 flex-shrink-0"
            />
            <span className="min-w-0 break-words">{item.actionItem}</span>
            <div className="text-sm">{item.assignee}</div>
            <div className="text-sm">{item.deadline}</div>
          </div>
        ))}
      </div>
    </div>
  );
}
