import { useState } from "react";
import { updateTodo, deleteTodo } from "../lib/api";

export interface TodoItem {
  id: string;
  assignee: string;
  actionItem: string;
  deadline: string;
  priority?: string;
  category?: string;
  completed?: boolean;
}

interface TodoListProps {
  todoItems: TodoItem[];
  meetingId?: string;
  onTodoUpdate?: () => void;
}

export default function TodoList({ todoItems, meetingId, onTodoUpdate }: TodoListProps) {
  const [items, setItems] = useState(todoItems);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editingTodo, setEditingTodo] = useState<Partial<TodoItem>>({});
  const [isUpdating, setIsUpdating] = useState(false);

  const toggleComplete = (id: string) => {
    setItems(
      items.map((item) =>
        item.id === id ? { ...item, completed: !item.completed } : item
      )
    );
  };

  const startEditing = (item: TodoItem) => {
    setEditingId(item.id);
    setEditingTodo({
      actionItem: item.actionItem,
      assignee: item.assignee === "담당자 미지정" ? "" : item.assignee,
      deadline: item.deadline,
      priority: item.priority || "보통",
      category: item.category || "일반"
    });
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditingTodo({});
  };

  const saveEdit = async () => {
    if (!meetingId || !editingId) return;

    try {
      setIsUpdating(true);
      const todoIndex = parseInt(editingId) - 1; // id는 1부터 시작하므로 -1

      const updatedData = {
        task: editingTodo.actionItem || "",
        assignee: editingTodo.assignee || "",
        deadline: editingTodo.deadline || "",
        priority: editingTodo.priority || "보통",
        category: editingTodo.category || "일반"
      };

      const response = await updateTodo(meetingId, todoIndex, updatedData);

      if (response.success) {
        // 로컬 상태 업데이트
        setItems(items.map(item => 
          item.id === editingId 
            ? {
                ...item,
                actionItem: updatedData.task,
                assignee: updatedData.assignee || "담당자 미지정",
                deadline: updatedData.deadline,
                priority: updatedData.priority,
                category: updatedData.category
              }
            : item
        ));
        
        setEditingId(null);
        setEditingTodo({});
        
        // 부모 컴포넌트에 업데이트 알림
        if (onTodoUpdate) {
          onTodoUpdate();
        }
      } else {
        alert("수정 실패: " + (response.error || "알 수 없는 오류"));
      }
    } catch (error) {
      console.error("Todo 수정 오류:", error);
      alert("수정 중 오류가 발생했습니다.");
    } finally {
      setIsUpdating(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!meetingId) return;
    
    if (!confirm("이 할 일을 삭제하시겠습니까?")) {
      return;
    }

    try {
      const todoIndex = parseInt(id) - 1; // id는 1부터 시작하므로 -1
      const response = await deleteTodo(meetingId, todoIndex);

      if (response.success) {
        // 로컬 상태에서 삭제
        setItems(items.filter(item => item.id !== id));
        
        // 부모 컴포넌트에 업데이트 알림
        if (onTodoUpdate) {
          onTodoUpdate();
        }
      } else {
        alert("삭제 실패: " + (response.error || "알 수 없는 오류"));
      }
    } catch (error) {
      console.error("Todo 삭제 오류:", error);
      alert("삭제 중 오류가 발생했습니다.");
    }
  };

  return (
    <div className="bg-white rounded-lg border border-gray-300 p-6">
      <h2 className="text-xl font-bold text-gray-800 mb-6">할 일 목록</h2>

      <div className="space-y-4">
        <div className="grid grid-cols-[auto_1fr_minmax(60px,80px)_minmax(80px,120px)_minmax(80px,100px)] gap-4 pb-2 border-b border-gray-200 text-sm font-medium text-gray-600">
          <div></div>
          <div>할 일</div>
          <div>담당자</div>
          <div>기한</div>
          <div>작업</div>
        </div>

        {items.map((item) => (
          <div
            key={item.id}
            className={`grid grid-cols-[auto_1fr_minmax(60px,80px)_minmax(80px,120px)_minmax(80px,100px)] gap-4 items-center py-2 ${
              item.completed ? "line-through text-gray-500" : "text-gray-900"
            }`}
          >
            <input
              type="checkbox"
              checked={item.completed || false}
              onChange={() => toggleComplete(item.id)}
              className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500 flex-shrink-0"
            />
            
            {/* 편집 모드 */}
            {editingId === item.id ? (
              <>
                <input
                  type="text"
                  value={editingTodo.actionItem || ""}
                  onChange={(e) => setEditingTodo({...editingTodo, actionItem: e.target.value})}
                  className="min-w-0 px-2 py-1 border border-gray-300 rounded text-sm"
                  placeholder="할 일"
                />
                <input
                  type="text"
                  value={editingTodo.assignee || ""}
                  onChange={(e) => setEditingTodo({...editingTodo, assignee: e.target.value})}
                  className="min-w-0 px-2 py-1 border border-gray-300 rounded text-sm"
                  placeholder="담당자"
                />
                <input
                  type="text"
                  value={editingTodo.deadline || ""}
                  onChange={(e) => setEditingTodo({...editingTodo, deadline: e.target.value})}
                  className="min-w-0 px-2 py-1 border border-gray-300 rounded text-sm"
                  placeholder="기한"
                />
                <div className="flex gap-1">
                  <button
                    onClick={saveEdit}
                    disabled={isUpdating}
                    className="px-2 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 disabled:opacity-50"
                  >
                    {isUpdating ? "저장중..." : "저장"}
                  </button>
                  <button
                    onClick={cancelEditing}
                    className="px-2 py-1 bg-gray-300 text-gray-700 text-xs rounded hover:bg-gray-400"
                  >
                    취소
                  </button>
                </div>
              </>
            ) : (
              <>
                <span className="min-w-0 break-words">{item.actionItem}</span>
                <div className="text-sm">{item.assignee}</div>
                <div className="text-sm">{item.deadline}</div>
                <div className="flex gap-1">
                  {meetingId && (
                    <>
                      <button
                        onClick={() => startEditing(item)}
                        className="px-2 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600"
                      >
                        수정
                      </button>
                      <button
                        onClick={() => handleDelete(item.id)}
                        className="px-2 py-1 bg-red-500 text-white text-xs rounded hover:bg-red-600"
                      >
                        삭제
                      </button>
                    </>
                  )}
                </div>
              </>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
