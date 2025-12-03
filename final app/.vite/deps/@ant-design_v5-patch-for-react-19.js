"use client";
import {
  require_client
} from "./chunk-OF6LXU6S.js";
import {
  unstableSetRender
} from "./chunk-PH4ZOQGD.js";
import "./chunk-CDGRQO3C.js";
import "./chunk-BSFGFYY7.js";
import "./chunk-5I2J475C.js";
import {
  __toESM
} from "./chunk-V4OQ3NZ2.js";

// node_modules/@ant-design/v5-patch-for-react-19/es/index.js
var import_client = __toESM(require_client());
unstableSetRender(function(node, container) {
  container._reactRoot || (container._reactRoot = (0, import_client.createRoot)(container));
  var root = container._reactRoot;
  root.render(node);
  return function() {
    return new Promise(function(resolve) {
      setTimeout(function() {
        root.unmount();
        resolve();
      }, 0);
    });
  };
});
//# sourceMappingURL=@ant-design_v5-patch-for-react-19.js.map
