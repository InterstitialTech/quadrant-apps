/*

  SwipeMachine.h
  Chris Chronopoulos, 20231218

*/

class SwipeMachine {

  uint8_t LEFT_CHAN = 0;
  uint8_t RIGHT_CHAN = 2;

  public:
    void update(QuadrantDSP *dsp);
    bool swipedLeft(void);
    bool swipedRight(void);

  private:
    bool _wasEngaged[4] = {false};
    bool _primedLeft = false;
    bool _primedRight = false;
    bool _swipedLeft = false;
    bool _swipedRight = false;

};

void SwipeMachine::update(QuadrantDSP *dsp) {

  _swipedLeft = false;
  _swipedRight = false;

  for (int i=0; i<4; i++) {

    if (!_wasEngaged[i] && dsp->isLidarEngaged(i)) { // rising edge

      if (i==LEFT_CHAN && _wasEngaged[RIGHT_CHAN]) {
        _primedLeft = true;
      } else if (i==RIGHT_CHAN && _wasEngaged[LEFT_CHAN]) {
        _primedRight = true;
      }

      _wasEngaged[i] = true;

    } else if (_wasEngaged[i] && !dsp->isLidarEngaged(i)) {  // falling edge

      if (i==LEFT_CHAN && _wasEngaged[RIGHT_CHAN]) {
        if (_primedRight) {
          _swipedRight = true;
          _primedRight= false;
        } else if (_primedLeft) {   // left fakeout
          _primedLeft = false;
        }
      } else if (i==RIGHT_CHAN && _wasEngaged[LEFT_CHAN]) {
        if (_primedLeft) {
          _swipedLeft = true;
          _primedLeft = false;
        } else if (_primedRight) {  // right fakeout
          _primedRight = false;
        }
      }

      _wasEngaged[i] = false;

    }
  }

}

bool SwipeMachine::swipedLeft(void) {

  return _swipedLeft;

}

bool SwipeMachine::swipedRight(void) {

  return _swipedRight;

}

