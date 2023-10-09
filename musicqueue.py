from table2ascii import table2ascii as t2a
from collections import deque
import logging  # Import the logging module

# Configure logging
logging.basicConfig(
    filename='musicqueue.log',  # Log file name
    level=logging.ERROR,        # Log only error messages and above
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class MusicQueue():
    queue = deque()
    current_index = 0  # Index of song currently playing (default is 0)

    # View a text output of the queue
    def view_queue(self):
        # If queue is empty return message
        if self.size() == 0:
            return "Queue is currently empty."

        queue_dict = {}
        for i, song in enumerate(self.queue):
            queue_dict.update({str(i+1): song[:50]})

        output = t2a(header=["Queue No", "Song"],
                     body=list(queue_dict.items()),
                     first_col_heading=True)
        
        return (f"Queue:\n```\n{output}\n```")

    # Add song to queue
    async def add_to_queue(self, song):
        self.queue.append(song)

    # Remove song from queue via song name
    def remove_from_queue_s(self, songname):
        try:
            self.queue.remove(songname[:50])
            return True
        except Exception as e:
            logging.error(f"Error while trying to remove from \
                          queue via value: {e}")
            return False

    # Remove song from queue via song position and return it
    def remove_from_queue_i(self, index):
        if index > self.size() or index < 0:
            logging.error(f"Error while trying to remove from \
                          queue via index: index out of range")
            return False

        value = self.queue[index]  # Find value at given index
        self.queue.remove(value)  # Remove element with given value

    def remove_next(self):
        return self.queue.popleft()

    # Move this song in the queue (index1 to index2)
    def move_song_i(self, songindex, newindex):
        return self.move_song(songindex, newindex)

    def move_song_s(self, newindex, songname):
        # Get the index of the song with matching name
        songindex = self.queue.index(songname)
        self.move_song(songindex, newindex)

    def move_song(self, songindex, newindex):
        if songindex > self.size() or songindex < 0 \
         or newindex > self.size() or newindex < 0:
            logging.error(f"Error while trying to move song: \
                          index out of range {songindex},{newindex}")
            return ("Song index is out of bounds")

        # Rotate the deque to bring the element to the front
        self.queue.rotate(-songindex)
        # Pop the element from the front
        song_to_move = self.queue.popleft()
        # Rotate the deque back
        self.queue.rotate(songindex)
        # Insert element into new position
        self.queue.insert(newindex, song_to_move)
        return True

    def size(self):
        return len(self.queue)
