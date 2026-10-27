import unittest
import re
from bs4 import BeautifulSoup

class TestSeatSelectionAndBookingLifecycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with open('/Users/aleksandr/BusLiner/passenger-cabinet.html', 'r', encoding='utf-8') as f:
            cls.html = f.read()
            cls.soup = BeautifulSoup(cls.html, 'html.parser')

    def test_booking_modal_elements_exist(self):
        modal = self.soup.find('div', id='bookingModal')
        self.assertIsNotNone(modal, "bookingModal must exist")

        btn_submit = self.soup.find(id='btnSubmitBooking')
        self.assertIsNotNone(btn_submit, "btnSubmitBooking must exist with id='btnSubmitBooking'")

        chips_container = self.soup.find(id='selectedSeatsChips')
        self.assertIsNotNone(chips_container, "selectedSeatsChips container must exist")

        seats_grid = self.soup.find(id='bookingSeatsGrid')
        self.assertIsNotNone(seats_grid, "bookingSeatsGrid container must exist")

    def test_profile_history_container_exists(self):
        history_list = self.soup.find(id='passengerHistoryTripList')
        self.assertIsNotNone(history_list, "passengerHistoryTripList must exist")

        history_count = self.soup.find(id='passengerHistoryCount')
        self.assertIsNotNone(history_count, "passengerHistoryCount must exist")

    def test_seat_removal_logic_does_not_block_on_single_seat(self):
        # Verify removeSelectedBookingSeat has NO check for length <= 1
        self.assertNotIn("if (selectedSeatsForBooking.length <= 1)", self.html,
                         "removeSelectedBookingSeat must NOT block when selectedSeatsForBooking.length <= 1")
        self.assertNotIn("if (selectedSeatsForBooking.length === 1)", self.html,
                         "selectBookingSeat must NOT block when selectedSeatsForBooking.length === 1")

    def test_occupied_seats_persistence_helpers_exist(self):
        self.assertIn("function getOccupiedSeatsForTrip", self.html)
        self.assertIn("function saveOccupiedSeatsForTrip", self.html)
        self.assertIn("busliner_occupied_seats_", self.html)

    def test_order_tab_and_history_feed_refresh(self):
        self.assertIn("function renderOrderTab", self.html)
        self.assertIn("function renderHistoryFeed", self.html)
        self.assertIn("saveOccupiedSeatsForTrip(selectedTripForBooking.id, selectedSeatsForBooking)", self.html)

    def test_sprinter_3d_cutaway_safety(self):
        with open('/Users/aleksandr/BusLiner/assets/sprinter-3d-model.js', 'r', encoding='utf-8') as f:
            js = f.read()
        # Verify inspectCutawaySeat is safely guarded with typeof check
        self.assertIn("typeof window.inspectCutawaySeat === 'function'", js)

if __name__ == '__main__':
    unittest.main()
