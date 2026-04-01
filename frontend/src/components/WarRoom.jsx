import PositionColumn from './PositionColumn'
import NotesDialog from './NotesDialog'
import AddPlayerDialog from './AddPlayerDialog'
import DeleteConfirmDialog from './DeleteConfirmDialog'
import './WarRoom.css'

const POSITIONS = ['QB', 'RB', 'WR', 'TE']

export default function WarRoom({
  rankings, dirty, onReorder, onSave,
  notesDialog, onNotesOpen, onNotesClose, onNotesUpdate,
  addDialog, onAddOpen, onAddClose, onAdd,
  deleteDialog, onDeleteOpen, onDeleteClose, onDelete,
}) {
  return (
    <div className="war-room">
      <header className="war-room-header">
        <div className="war-room-title">🏈 WAR ROOM</div>
        <div className="war-room-status">
          {dirty && <span className="unsaved-indicator">● UNSAVED</span>}
        </div>
        <button className="save-button" onClick={onSave}>SAVE</button>
      </header>

      <div className="war-room-columns">
        {POSITIONS.map(pos => (
          <PositionColumn
            key={pos}
            position={pos}
            players={rankings[pos]}
            onReorder={onReorder}
            onNotesOpen={onNotesOpen}
            onAddOpen={onAddOpen}
            onDeleteOpen={onDeleteOpen}
          />
        ))}
      </div>

      {notesDialog && (
        <NotesDialog
          isOpen={true}
          player={notesDialog.player}
          position={notesDialog.position}
          onSave={(notes) => onNotesUpdate(notesDialog.position, notesDialog.player.position_rank, notes)}
          onClose={onNotesClose}
        />
      )}

      {addDialog && (
        <AddPlayerDialog
          isOpen={true}
          position={addDialog.position}
          tier={addDialog.tier}
          onAdd={onAdd}
          onClose={onAddClose}
        />
      )}

      {deleteDialog && (
        <DeleteConfirmDialog
          isOpen={true}
          player={deleteDialog.player}
          position={deleteDialog.position}
          onConfirm={() => onDelete(deleteDialog.position, deleteDialog.player.position_rank)}
          onClose={onDeleteClose}
        />
      )}
    </div>
  )
}
