/*

  triangulation.ino
    chrono [20240106]
    pitch, roll, hits, and swipes

*/

#include "Quadrant.h"
Quadrant quadrant;

#include "SwipeMachine.h"
SwipeMachine swiper;

bool was_engaged[4] = {false};
uint32_t time_engagement[4] = {0};

void setup(void) {

  quadrant.begin();
  quadrant.enableFilter(true);
  quadrant.run();

}

void loop(void) {

  if (quadrant.newDataReady()) {

    // update local state machine and status report
    quadrant.update();

    // set indicator leds
    for (int i=0; i<4; i++) {
      if (quadrant.isLidarEngaged(i)) {
        quadrant.setLed(i, HIGH);
      } else {
        quadrant.setLed(i, LOW);
      }
    }

    // analyze swipe
    swiper.update(&quadrant.dsp);
    if (swiper.swipedLeft()) {
      quadrant.out.addEventToReport("swl");
    }
    if (swiper.swipedRight()) {
      quadrant.out.addEventToReport("swr");
    }

    // analyize pluck
    uint32_t dt;
    for (int i=0; i<4; i++) {
      if (quadrant.isLidarEngaged(i)) {
        if (!was_engaged[i]) {
          time_engagement[i] = quadrant.getTimestamp();
        }
        was_engaged[i] = true;
      } else {
        if (was_engaged[i]) {
          dt = quadrant.getTimestamp() - time_engagement[i];
          if ((dt < 150000) && (dt > 30000)) {
            switch (i) {
              case 0:
                quadrant.out.addEventToReport("hit0");
                break;
              case 1:
                quadrant.out.addEventToReport("hit1");
                break;
              case 2:
                quadrant.out.addEventToReport("hit2");
                break;
              case 3:
                quadrant.out.addEventToReport("hit3");
                break;
              default:
                break;
            }
          }
        }
        was_engaged[i] = false;
      }
    }

    // print a JSON status report to the USB serial monitor
    quadrant.printReportToSerial();

  }

}

