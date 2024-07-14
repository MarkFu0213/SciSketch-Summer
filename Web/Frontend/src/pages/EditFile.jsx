import { useCallback, useEffect, useState } from "react";
import Quill from "quill";
import "quill/dist/quill.snow.css";
import { useParams, useNavigate } from "react-router-dom";
import axios from "axios";
import ImageResize from "quill-image-resize-module-react";
import "./EditFile.css";

// Register the ImageResize module with Quill
Quill.register("modules/imageResize", ImageResize);

const SAVE_INTERVAL_MS = 2000;
const TOOLBAR_OPTIONS = [
  [{ header: [1, 2, 3, 4, 5, 6, false] }],
  [{ font: [] }],
  [{ list: "ordered" }, { list: "bullet" }],
  ["bold", "italic", "underline"],
  [{ color: [] }, { background: [] }],
  [{ script: "sub" }, { script: "super" }],
  [{ align: [] }],
  ["image", "blockquote", "code-block"],
  ["clean"],
];

export default function TextEditor() {
  const { id: documentId } = useParams();
  const navigate = useNavigate();
  const [quill, setQuill] = useState(null);
  const [fileName, setFileName] = useState(null);

  useEffect(() => {
    const fetchDocument = async () => {
      try {
        const response = await axios.get(
          // `http://localhost:5000/api/documents/${documentId}`
          `http://127.0.0.1:5000/api/documents/${documentId}`
        );
        if (quill) {
          quill.setContents(response.data.content);
          quill.enable();
        }
        setFileName(response.data.name);
      } catch (error) {
        console.error("Error fetching document:", error);
      }
    };

    fetchDocument();
  }, [documentId, quill]);

  useEffect(() => {
    if (quill == null) return;

    const interval = setInterval(() => {
      saveDocument();
    }, SAVE_INTERVAL_MS);

    return () => {
      clearInterval(interval);
      saveDocument(); // Save document one last time on component unmount
    };
  }, [quill, documentId, fileName]);

  const saveDocument = async () => {
    if (!quill) return;
    try {
      // await axios.post(`http://localhost:5000/api/documents/${documentId}`, {
      await axios.post(`http://127.0.0.1:5000/api/documents/${documentId}`, {
        content: quill.getContents(),
        name: fileName,
      });
    } catch (error) {
      console.error("Error saving document:", error);
    }
  };

  const wrapperRef = useCallback((wrapper) => {
    if (wrapper == null) return;

    wrapper.innerHTML = "";
    const editor = document.createElement("div");
    wrapper.append(editor);
    const q = new Quill(editor, {
      theme: "snow",
      modules: {
        toolbar: TOOLBAR_OPTIONS,
        imageResize: {
          modules: ["Resize", "DisplaySize"],

          displayStyles: {
            backgroundColor: "black",
            border: "none",
            color: "white",
            // other camelCase styles for size display
          },
          toolbarStyles: {
            backgroundColor: "black",
            border: "none",
            color: "white",
            // other camelCase styles for size display
          },
          toolbarButtonStyles: {
            // ...
          },
          toolbarButtonSvgStyles: {
            // ...
          },
        },
      },
    });

    q.disable();
    setQuill(q);
  }, []);

  useEffect(() => {
    if (quill == null) return;

    const handleImageRightClick = (event) => {
      const target = event.target;
      console.log("Target:", target);
      if (target.closest("img")) {
        // Handle right-click logic for the selected image
        console.log("Image right-clicked:", target.src);
      }
    };

    const quillContainer = quill.container;
    quillContainer.addEventListener("contextmenu", handleImageRightClick);

    return () => {
      quillContainer.removeEventListener("contextmenu", handleImageRightClick);
    };
  }, [quill]);

  const handleBackToHome = () => {
    saveDocument(); // Save document before navigating back
    navigate("/");
  };

  const handleFileNameChange = (e) => {
    setFileName(e.target.value);
  };

  return (
    <div className="cont">
      <div className="top-bar">
        <button onClick={handleBackToHome} className="back-button">
          Home
        </button>
        <input
          type="text"
          value={fileName}
          onChange={handleFileNameChange}
          className="file-name-input"
        />
      </div>
      <div className="container" ref={wrapperRef}></div>
    </div>
  );
}
