import PositionColumn from './PositionColumn'
import NotesDialog from './NotesDialog'
import AddPlayerDialog from './AddPlayerDialog'
import DeleteConfirmDialog from './DeleteConfirmDialog'
import SaveAsDialog from './SaveAsDialog'
import LoadDialog from './LoadDialog'
import ResetConfirmDialog from './ResetConfirmDialog'
import SetDefaultConfirmDialog from './SetDefaultConfirmDialog'
import ExitDraftConfirmDialog from './ExitDraftConfirmDialog'
import SearchBar from './SearchBar'
import './WarRoom.css'

const POSITIONS = ['QB', 'RB', 'WR', 'TE']

export default function WarRoom({
  rankings, dirty, profileName, mode, isDraft, hasPicks,
  getDraftStatus, onStatusClick, onEnterDraft, onExitDraft,
  exitDraftDialog, onConfirmExitDraft, onCancelExitDraft,
  searchQuery, onSearchChange, searchResults, onSelectResult,
  onReorder, onSave,
  onSaveAsOpen, onLoadOpen, onResetOpen, onSetDefaultOpen,
  notesDialog, onNotesOpen, onNotesClose, onNotesUpdate,
  addDialog, onAddOpen, onAddClose, onAdd,
  deleteDialog, onDeleteOpen, onDeleteClose, onDelete,
  saveAsDialog, onSaveAs, onSaveAsClose,
  loadDialog, onLoad, onLoadClose,
  resetDialog, onReset, onResetClose,
  setDefaultDialog, onSetDefault, onSetDefaultClose,
}) {
  const rootClass = [
    'war-room',
    isDraft && 'draft-mode',
    isDraft && hasPicks && 'has-picks',
  ].filter(Boolean).join(' ')

  return (
    <div className={rootClass}>
      <header className="war-room-header">
        <div className="war-room-title">🏈 WAR ROOM</div>

        <div className="mode-toggle">
          <button
            className={`mode-toggle-btn ${mode === 'warroom' ? 'active-warroom' : ''}`}
            onClick={isDraft ? onExitDraft : undefined}
          >
            WAR ROOM
          </button>
          <button
            className={`mode-toggle-btn ${mode === 'draft' ? 'active-draft' : ''}`}
            onClick={!isDraft ? onEnterDraft : undefined}
          >
            DRAFT
          </button>
        </div>

        <SearchBar
          query={searchQuery}
          onChange={onSearchChange}
          results={searchResults}
          onSelectResult={onSelectResult}
          isDraft={isDraft}
          getDraftStatus={getDraftStatus}
        />

        <span className="profile-name">{profileName}</span>

        {!isDraft && (
          <>
            <div className="war-room-status">
              {dirty && <span className="unsaved-indicator">● UNSAVED</span>}
            </div>
            <div className="toolbar">
              <button className="save-button" onClick={onSave}>SAVE</button>
              <button className="toolbar-btn" onClick={onSaveAsOpen}>SAVE AS</button>
              <button className="toolbar-btn" onClick={onLoadOpen}>LOAD</button>
              <button className="toolbar-btn toolbar-btn-danger" onClick={onResetOpen}>RESET</button>
              <button className="toolbar-btn" onClick={onSetDefaultOpen}>★ SET DEFAULT</button>
            </div>
          </>
        )}
      </header>

      <div className="war-room-columns">
        {POSITIONS.map(pos => (
          <PositionColumn
            key={pos}
            position={pos}
            players={rankings[pos]}
            isDraft={isDraft}
            getDraftStatus={getDraftStatus}
            onStatusClick={onStatusClick}
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

      <SaveAsDialog isOpen={saveAsDialog} onSave={onSaveAs} onClose={onSaveAsClose} />
      <LoadDialog isOpen={loadDialog} dirty={dirty} onLoad={onLoad} onClose={onLoadClose} />
      <ResetConfirmDialog isOpen={resetDialog} onConfirm={onReset} onClose={onResetClose} />
      <SetDefaultConfirmDialog isOpen={setDefaultDialog} onConfirm={onSetDefault} onClose={onSetDefaultClose} />
      <ExitDraftConfirmDialog isOpen={exitDraftDialog} onConfirm={onConfirmExitDraft} onClose={onCancelExitDraft} />
    </div>
  )
}
