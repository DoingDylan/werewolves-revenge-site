import React, { useState, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import interactionPlugin from '@fullcalendar/interaction';
// Note: FullCalendar packages no longer export CSS via subpath imports
// Import calendar styles via a global stylesheet or CDN link in the layout instead

interface Event {
  id: string;
  title: string;
  description?: string;
  start_datetime: string;
  end_datetime?: string;
  event_type?: string;
  status?: string;
}

interface SelectedEvent extends Event {
  startDate?: string;
  endDate?: string;
}

export default function EventCalendar() {
  const [events, setEvents] = useState<Event[]>([]);
  const [selectedEvent, setSelectedEvent] = useState<SelectedEvent | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    const fetchEvents = async () => {
      try {
        const response = await fetch('/api/events.json');
        const data = await response.json();
        setEvents(data);
      } catch (error) {
        console.error('Failed to fetch events:', error);
      }
    };

    fetchEvents();
  }, []);

  const handleEventClick = (event: Event) => {
    const startDate = new Date(event.start_datetime).toLocaleDateString();
    const endDate = event.end_datetime 
      ? new Date(event.end_datetime).toLocaleDateString() 
      : startDate;

    setSelectedEvent({
      ...event,
      startDate,
      endDate,
    });
    setIsModalOpen(true);
  };

  const calendarEvents = events.map((event) => ({
    id: event.id,
    title: event.title,
    start: event.start_datetime,
    end: event.end_datetime,
  }));

  return (
    <div className="w-full max-w-4xl mx-auto p-4 mt-24" style={{ marginTop: '88px' }}>
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h2 className="text-2xl font-bold mb-4 text-red-800">Werewolves Revenge Events</h2>
        
        <div className="calendar-wrapper">
          <FullCalendar
            plugins={[dayGridPlugin, interactionPlugin]}
            initialView="dayGridMonth"
            events={calendarEvents}
            eventClick={(info) => {
              const event = events.find(e => e.id === info.event.id);
              if (event) handleEventClick(event);
            }}
            headerToolbar={{
              left: 'prev,next today',
              center: 'title',
              right: '',
            }}
            height="auto"
            contentHeight="auto"
          />
        </div>
      </div>

      {isModalOpen && selectedEvent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
            <div className="flex justify-between items-start mb-4">
              <h3 className="text-xl font-bold text-gray-800">{selectedEvent.title}</h3>
              <button
                onClick={() => setIsModalOpen(false)}
                className="text-gray-500 hover:text-gray-700 font-bold text-lg"
              >
                ✕
              </button>
            </div>

            <div className="space-y-3 text-gray-700">
              {selectedEvent.description && (
                <div>
                  <p className="font-semibold text-gray-800">Description</p>
                  <p className="text-gray-600">{selectedEvent.description}</p>
                </div>
              )}

              <div>
                <p className="font-semibold text-gray-800">Start Date</p>
                <p className="text-gray-600">{selectedEvent.startDate}</p>
              </div>

              <div>
                <p className="font-semibold text-gray-800">End Date</p>
                <p className="text-gray-600">{selectedEvent.endDate}</p>
              </div>

              {selectedEvent.event_type && (
                <div>
                  <p className="font-semibold text-gray-800">Type</p>
                  <p className="text-gray-600">{selectedEvent.event_type}</p>
                </div>
              )}

              {selectedEvent.status && (
                <div>
                  <p className="font-semibold text-gray-800">Status</p>
                  <p className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${
                    selectedEvent.status === 'confirmed' 
                      ? 'bg-green-100 text-green-800' 
                      : selectedEvent.status === 'pending'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}>
                    {selectedEvent.status}
                  </p>
                </div>
              )}
            </div>

            <button
              onClick={() => setIsModalOpen(false)}
              className="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      )}

      <style>{`
        .calendar-wrapper .fc {
          font-family: inherit;
          color: #111827 !important;
        }

        .calendar-wrapper .fc *,
        .calendar-wrapper .fc a {
          color: #111827 !important;
        }

        .calendar-wrapper .fc button {
          text-transform: capitalize;
        }

        .calendar-wrapper .fc-event {
          cursor: pointer;
          background-color: #2563eb;
          border-color: #1d4ed8;
          color: #fff !important;
        }

        .calendar-wrapper .fc-event:hover {
          background-color: #1d4ed8;
          border-color: #1e40af;
        }

        /* Improve visibility of headers, day numbers, and grid */
        .calendar-wrapper .fc .fc-col-header-cell .fc-col-header-cell-cushion,
        .calendar-wrapper .fc .fc-col-header-cell .fc-col-header-cell-cushion a,
        .calendar-wrapper .fc .fc-daygrid-day-number {
          color: #111827 !important;
          font-weight: 700;
        }

        .calendar-wrapper .fc .fc-col-header-cell {
          background: #f8fafc !important;
        }

        .calendar-wrapper .fc .fc-scrollgrid-section-header {
          color: #111827 !important;
        }

        .calendar-wrapper .fc .fc-daygrid-event-main {
          color: #fff !important;
        }

        .calendar-wrapper .fc .fc-toolbar-title {
          color: #111827 !important;
          font-weight: 700;
        }

        .calendar-wrapper .fc .fc-daygrid-day-bg {
          background: transparent;
        }

        /* Force all calendar text to dark for visibility */
        .calendar-wrapper .fc,
        .calendar-wrapper .fc * {
          color: #111827 !important;
          fill: #111827 !important;
          stroke: #111827 !important;
        }

        .calendar-wrapper .fc a,
        .calendar-wrapper .fc button {
          color: #111827 !important;
        }
      `}</style>
    </div>
  );
}
