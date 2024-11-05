'use client'

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Release } from "@/lib/types";
import { ChangeEvent, useEffect, useMemo, useState } from "react";
import _ from 'lodash';
import { Header } from "@/components/ui/header";
import { useSearchParams } from "next/navigation";
import { releaseTypes } from "@/lib/const";

interface SelectOption {
  [key: string]: string;
}

const YearSelect = (props: {
  onChange: (name: string, value: string) => void;
}) => {
  const startYear = 1982;
  const endYear = 2024;

  return (
    <Select onValueChange={(s) => props.onChange('year', s)}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Year" />
      </SelectTrigger>
      <SelectContent>
        {Array.from({ length: endYear - startYear + 1 }, (_, index) => {
          const year = startYear + index;
          return (
            <SelectItem key={index} value={`${year}`}>{year}</SelectItem>
          );
        })}
      </SelectContent>
    </Select>
  )
};

const FormSelect = (props: {
  formKey: string;
  label: string;
  options: SelectOption[];
  onChange: (name: string, value: string) => void;
}) => (
  <Select onValueChange={(c) => props.onChange(props.formKey, c)}>
    <SelectTrigger className="w-[180px]">
      <SelectValue placeholder={props.label} />
    </SelectTrigger>
    <SelectContent>
      { props.options.map((o, i) => (
        <SelectItem key={i} value={o.value}>
          {o.name}
        </SelectItem>
      ))}
    </SelectContent>
  </Select>
)

const FormInput = (props: {
  formKey: ReleaseKey;
  placeholder: string;
  typing: boolean;
  onUpdate: (key: ReleaseKey, value: string | null) => void;
  setTyping: (typing: boolean) => void;
}) => {
  const handleInputChange = (key: ReleaseKey, e: ChangeEvent<HTMLInputElement>) => {
    props.onUpdate(key, e.target.value === '' ? null : e.target.value)

    if (props.typing) {
      props.setTyping(false);
    }
  }

  const debounceInput = _.debounce(handleInputChange, 1000)

  return (
    <Input
      onChange={(e) => {
        if (!props.typing) {
          props.setTyping(true);
        }

        debounceInput(props.formKey, e);
      }}
      type="text"
      placeholder={props.placeholder}
    />
  )

}

type ReleaseKey = keyof Release;

export default function Page() {
  const [releaseForm, setReleaseForm] = useState<Release>({ } as Release);
  const [typing, setTyping] = useState<boolean>(false);
  const searchParams = useSearchParams();

  useEffect(() => {
    const band_id = searchParams.get("band_id");

    if (band_id) {
      setReleaseForm({
        ...releaseForm,
        band_id
      });
    }
  }, [searchParams])

  const requiredFields: ReleaseKey[] = ["name", "type"];

  const handleSelect = (key: string, value: string) => {
    setReleaseForm({
      ...releaseForm,
      [key]: value
    })
  }

  const handleSubmit = (release: Release) => {
    // const submitBand = async (params: {
    //   release: Release
    // }) => {
    //   const response = await fetch(`${process.env.NEXT_PUBLIC_API_URI}:${process.env.NEXT_PUBLIC_API_PORT}/band/create`, {
    //     method: "POST",
    //     body: JSON.stringify(params.release),
    //     headers: {
    //       "Content-Type": "application/json"
    //     }
    //   })

    //   return response.json();
    // }

    // submitBand({ release }).then((res) => {
    //   console.log(res)
    // })
  }

  const submitDisabled = useMemo(() => {
    let disabled = false;

    requiredFields.forEach((f: ReleaseKey) => {
      if (releaseForm[f] === null || typeof releaseForm[f] === "undefined" ) {
        disabled = true;
      }
    })

    return disabled;
  }, [releaseForm]);

  const updateForm = (key: ReleaseKey, value: string | null) => {
    setReleaseForm({
      ...releaseForm,
      [key]: value
    })
  }

  return (
    <main className="py-[1rem] flex-col">
      <Header />
      <div className="py-[1rem] w-full">
        <Separator />
      </div>
      <div className="flex flex-col gap-[1rem] p-[1rem]">
        <div className="flex flex-row">
          <div className="flex flex-col gap-[1rem]">
            <span className="text-4xl">Add Release</span>
            <FormInput
              formKey="name"
              onUpdate={updateForm}
              placeholder="Name"
              setTyping={setTyping}
              typing={typing}
            />
            <YearSelect onChange={handleSelect} />
            <FormInput
              formKey="label"
              onUpdate={updateForm}
              placeholder="Label"
              setTyping={setTyping}
              typing={typing}
            />
            <FormSelect
              formKey="type"
              label="Release Type"
              onChange={handleSelect}
              options={releaseTypes}
            />
            <Button
              disabled={submitDisabled || typing}
              onClick={() => handleSubmit(releaseForm)}
            >
              Submit
            </Button>
          </div>
        </div>
        <span>{JSON.stringify(releaseForm)}</span>
      </div>
    </main>
  );
}