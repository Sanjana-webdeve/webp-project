import React, { useState, useEffect } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useRouter } from "next/router";

const QuizCards = () => {
  const [defaultNameForNonLogUser, setDefaultNameForNonLogUser] = useState("");
  const [defaultAvatarForUser, setDefaultAvatarForUser] = useState("");
  const router = useRouter();

  useEffect(() => {
    let logedInUserName = "";
    if (logedInUserName !== "") {
      setDefaultNameForNonLogUser("");
    } else {
      const storedName = localStorage.getItem("_turtleDiaryDefaultUserName");
      if (storedName) {
        setDefaultNameForNonLogUser(storedName);
      } else {
        const defaultName = "Joon5461";
        setDefaultNameForNonLogUser(defaultName);
        localStorage.setItem("_turtleDiaryDefaultUserName", defaultName);
      }
    }

    let loggedInUserAvatar = "";
    if (loggedInUserAvatar !== "") {
      setDefaultAvatarForUser("");
    } else {
      const storedAvatar = localStorage.getItem("_turtleDiaryDefaultUserAvatar");
      if (storedAvatar) {
        setDefaultAvatarForUser(storedAvatar);
      } else {
        const defaultAvatar = "https://media.turtlediary.com/assets/avatars/user-avatar/Hero-Masks/hero-msk-24.png";
        setDefaultAvatarForUser(defaultAvatar);
        localStorage.setItem("_turtleDiaryDefaultUserAvatar", defaultAvatar);
      }
    }
  }, []);

  const handleCardClick = () => {
    router.push("/nextPage"); // Replace with your actual next page route
  };

  return (
    <div className="grid grid-cols-3 gap-4 p-4">
      <Card onClick={handleCardClick} className="cursor-pointer hover:shadow-lg transition">
        <CardContent className="flex flex-col items-center p-4">
          <img src={defaultAvatarForUser} alt="Avatar" className="w-16 h-16 rounded-full" />
          <p className="mt-2">{defaultNameForNonLogUser}</p>
          <Button onClick={handleCardClick} className="mt-4">Next</Button>
        </CardContent>
      </Card>
    </div>
  );
};

export default QuizCards;
